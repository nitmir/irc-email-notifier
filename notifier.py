#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License version 2 for
# more details.
#
# You should have received a copy of the GNU General Public License version 2
# along with this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import socket, imaplib2, time, re, email
import email.parser
from threading import *

class ThreadDead(Exception):
  def __init__(self):
    pass

class Idler(object):
  def __init__(self, conn, notifier):
    self.thread = Thread(target=self.idle)
    self.M = conn
    self.notifier=notifier
    self.event = Event()

  def start(self):
    self.thread.start()
    
  def stop(self):
    # This is a neat trick to make thread end. Took me a 
    # while to figure that one out!
    self.event.set()

  def join(self):
    self.thread.join()

  def test(self):
    return self.thread.is_alive()

  def format_header(self, header_format, str):
    keys=[i.lower() for i in str.keys()]
    header=header_format[0].lower()
    format=header_format[1]
    if not header in keys:
      print("%s not found" % header)
      return ""
    def safe_unicode(str, charset):
      try:
        return unicode(str, charset)
      except UnicodeDecodeError:
        return unicode("%r" % str)
    ret=' '.join([safe_unicode(i[0], i[1]) if i[1] else safe_unicode(i[0], self.notifier.charset)
        for i in email.Header.decode_header(str[header])])
# Old hack because of some malformed internationalized header
# but it create even more issues...
#                  re.sub(
#                      r"(=\?[^ ]*\?q\?[^ ]\?=)(?!\n)(?!$)",
#                      r"\1 ",
#                      str[header]
#                  )
    if header=='from':
      ret=re.sub('"?([^"]*)"? <(.*)>','\\1', ret)
    ret = (format % ret)

    if header_format[2:]:
        match, replace = header_format[2]
        ret = re.sub(match, replace, ret)
    return ret

  def idle(self):
    self.needsync = True
    self.event.set()
    while True:
      # Because the function sets the needsync variable,
      # this helps escape the loop without doing 
      # anything if the stop() is called. Kinda neat 
      # solution.
      if self.needsync:
        self.event.clear()
        self.dosync()
      # This is part of the trick to make the loop stop 
      # when the stop() command is given
      if self.event.isSet():
        return
      self.needsync = False
      # A callback method that gets called when a new 
      # email arrives. Very basic, but that's good.
      def callback(args):
        if not self.event.isSet():
          self.needsync = True
          self.event.set()
      # Do the actual idle call. This returns immediately, 
      # since it's asynchronous.
      self.M.idle(callback=callback)
      # This waits until the event is set. The event is 
      # set by the callback, when the server 'answers' 
      # the idle call and the callback function gets 
      # called.
      self.event.wait()

  # The method that gets called when a new email arrives. 
  # Replace it with something better.
  def dosync(self):
    try:
        a,b=self.M.sort('DATE', 'UTF-8', 'UNSEEN')
    except:
        a,b=self.M.search('UTF-8', 'UNSEEN')
    if a=='OK' and len(b)>0 and len(b[0])>0:
      #print(b)
      flood_excess=0
      for id in b[0].split():
        data=self.M.fetch(id,'(RFC822)')
        if data[1][0][0:len(id)]==id:
          header_data = data[1][1][1]
        else:
          header_data = data[1][0][1]
        parser = email.parser.HeaderParser()
        msg = parser.parsestr(header_data)
        msg = ''.join([self.format_header(header, msg) for header in self.notifier.headers])
        for chan in self.notifier.noticed:
          self.notifier.notice(chan.split(' ',1)[0], msg)
          flood_excess+=1
          if flood_excess>=5:
            time.sleep(2)
    elif a!='OK':
      print(a)


class Notifier(object):
  def __init__(self, network, chans, nick, host, user, password, box, port=6667, debug=0, headers=[['Subject','%s']], irc_timeout=360.0, notice=[], charset='utf-8', use_ssl=True, nickserv_pass=None):
    self.chans=chans
    self.noticed=notice
    self.noticed.extend(chans)
    self.nick=nick
    self.headers=headers
    nick_int=0
    nick_bool=False
    nick_next=0
    connected=False
    self.charset=charset
    self.irc=None
    self.idler=None
    self.M=None
    self.debug=debug
    while True:
      try:
        self.irc = socket.socket ( socket.AF_INET, socket.SOCK_STREAM )
        self.irc.settimeout(irc_timeout)
        print("Connection to irc")
        self.irc.connect ( ( network, port ) )
        #print(self.irc.recv ( 4096 ))
        print("Connect to imap")
        if use_ssl:
            self.M = imaplib2.IMAP4_SSL(host,debug=debug)
        else:
            self.M = imaplib2.IMAP4(host,debug=debug)
        print("Login")
        self.M.login(user,password)
        print("Selecting %s" % box)
        self.M.select(box)
        self.idler = Idler(self.M,self)
        self.send ( u'USER %s %s %s :Python IRC' % (nick,nick,nick) )
        self.send ( u'NICK %s' % nick )
        self.idler.start()
        while True:
          data = self.irc.recv ( 4096 )
          if len(data)==0:
            break
          data = data.split("\n")
          for data in data:
            if self.debug!=0:
              try:
                print(data)
              except:
                pass
            code=data.split(' ')
            if len(code)>1:
              code=code[1]
            else:
              code=0
            if code in [ '004', '376' ] and not connected:
               connected=True
               if nickserv_pass:
                    self.say(u'nickserv',u'IDENTIFY %s' % nickserv_pass)
                    time.sleep(0.5)
               for chan in self.chans:
                 print("Join %s" % chan)
                 self.send (u'JOIN %s' % chan )
            elif code=='433': # Nickname is already in use
              if not connected:
                self.send ( u'NICK %s%s' % (nick,nick_int) )
                nick_int+=1
              else:
                nick_next = time.time() + 10
              nick_bool=True
            elif code=='INVITE':
              chan=data.split(':',2)[2].strip()
              print("Invited on %s." % chan)
              if chan.lower() in [ chan.lower().split(' ', 1)[0].strip() for chan in self.chans]:
                print("Join %s" % chan)
                self.send (u'JOIN %s' % chan )

            if not self.idler.test():
              raise ThreadDead()

            if data.find ( b'PING' ) != -1:
              self.irc.send ( b'PONG ' + data.split() [ 1 ] + b'\r\n' )

            if connected:
              if nick_bool and time.time()>nick_next:
                self.send ( u'NICK %s' % nick )
                nick_bool=False
      finally:
        if self.irc:
            try: self.irc.close()
            except: pass
        if self.idler:
            try: self.idler.stop()
            except: pass
            try: self.idler.join()
            except: pass
        if self.M:
            try: self.M.close()
            except: pass
            try: self.M.logout()
            except: pass
            try: self.M.shutdown()
            except: pass
        time.sleep(2)

  def say(self,chan,str):
    msg=u'PRIVMSG %s :%s\r\n' % (chan,str)
    if self.debug!=0: print(msg.encode(self.charset))
    self.irc.send (msg.encode(self.charset))
  def notice(self,chan,str):
    msg=u'NOTICE %s :%s\r\n' % (chan,str)
    if self.debug!=0: print(msg.encode(self.charset))
    self.irc.send (msg.encode(self.charset))
  def send(self,str):
    msg=u'%s\r\n' % (str)
    if self.debug!=0: print(msg.encode(self.charset))
    self.irc.send (msg.encode(self.charset))
  


if __name__ == '__main__' :
  import sys
  import os
  import imp

  params_name = Notifier.__init__.func_code.co_varnames[:Notifier.__init__.func_code.co_argcount][1:]
  default_args = Notifier.__init__.func_defaults
  argc = len(params_name) - len(default_args)
  params = dict([(params_name[i], None if i < argc else default_args[i - argc]) for i in range(0, len(params_name))])

  def get_param(str):
    ret = None
    if str in sys.argv:
      i = sys.argv.index(str)
      if len(sys.argv)>i:
         ret = sys.argv[i+1]
         del(sys.argv[i+1])
      del(sys.argv[i])
    return ret

  def check_params(arg):
    if params[arg]: return None
    else: raise ValueError("Parameter %s is mandatory" % arg)

  confdir = get_param('--confdir') or os.path.dirname(os.path.realpath(__file__))
  pidfile = get_param('--pidfile')

  if len(sys.argv)>1:
    module = imp.load_source('config', confdir + "/" + sys.argv[1])
    params.update(module.params)

  try:
    map(check_params, params_name[:argc])
  except (ValueError,) as error:
    sys.stderr.write("%s\n" % error)
    exit(1)

  if pidfile:
    f = open(pidfile, 'w')
    f.write(os.getpid())
    f.close()

  try:
    Notifier(**params)
  except (KeyboardInterrupt,):
    exit(0)

