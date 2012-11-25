#!/usr/bin/env python
# -*- coding: utf-8 -*-
import socket, imaplib2, time, re, email
import email.parser
from threading import *





def format_header(header_format,str):
  keys=[i.lower() for i in str.keys()]
  header=header_format[0].lower()
  format=header_format[1]
  if not header in keys:
    print("%s not found" % header)
    return ""
  ret=' '.join([unicode(i[0],i[1]) if i[1] else i[0] for i in email.Header.decode_header(str[header])])
  if header=='from':
    ret=re.sub(' <(.*)>','', ret)
  return (format % ret)



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
    a,b=self.M.sort('DATE', 'UTF-8', 'UNSEEN')
    if a=='OK' and len(b)>0 and len(b[0])>0:
      print(b)
      flood_excess=0
      for id in b[0].split():
        data=self.M.fetch(id,'(RFC822)')
        if data[1][0][0:len(id)]==id:
          header_data = data[1][1][1]
        else:
          header_data = data[1][0][1]
        parser = email.parser.HeaderParser()
        msg = parser.parsestr(header_data)
        msg = ''.join([format_header(header, msg) for header in self.notifier.headers])
        for chan in self.notifier.noticed:
          self.notifier.notice(chan,msg)
          flood_excess+=1
          if flood_excess>=5:
            time.sleep(2)
    elif a!='OK':
      print(a)


class Notifier(object):
  def __init__(self, network, chans, nick, host, user, password, box, port=6667,debug=0,headers=[['Subject','%s']],irc_timeout=360.0,notice=[],charset='utf-8',use_ssl=True):
    self.chans=chans
    self.noticed=notice
    self.noticed.extend(chans)
    self.nick=nick
    self.headers=headers
    nick_int=0
    nick_bool=False
    self.charset=charset
    while True:
      try:
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
        self.irc = socket.socket ( socket.AF_INET, socket.SOCK_STREAM )
        self.irc.settimeout(irc_timeout)
        print("Connection to irc")
        self.irc.connect ( ( network, port ) )
        print(self.irc.recv ( 4096 ))
        self.send ( 'USER %s %s %s :Python IRC' % (nick,nick,nick) )
        self.send ( 'NICK %s' % nick )
        self.idler.start()
        while True:
          data = self.irc.recv ( 4096 )
          if len(data)==0:
            break
          data = data.split("\n")
          for data in data:
            code=data.split(' ')
            if len(code)>1:
              code=code[1]
            else:
              code=0
            if code=='004':
               for chan in self.chans:
                 print('Join %s' % chan)
                 self.send (('JOIN %s' % chan ))
            elif code=='433':
              self.send ( 'NICK %s%s' % (nick,nick_int) )
              nick_int+=1
              nick_bool=True
            if debug!=0:
              try:
                print(data)
              except:
                pass
            if not self.idler.test():
              raise ThreadDead()
            if nick_bool:
              self.send ( 'NICK %s' % nick )
              nick_bool=False
            if data.find ( b'PING' ) != -1:
              self.irc.send ( b'PONG ' + data.split() [ 1 ] + b'\r\n' )
      finally:
        self.irc.close()
        self.idler.stop()
        self.idler.join()
        self.M.close()
        self.M.logout()
        self.M.shutdown()
        time.sleep(2)

  def say(self,chan,str):
    msg='PRIVMSG %s :%s\r\n' % (chan,str)
    self.irc.send (msg.encode(self.charset))
  def notice(self,chan,str):
    msg='NOTICE %s :%s\r\n' % (chan,str)
    self.irc.send (msg.encode(self.charset))
  def send(self,str):
    msg='%s\r\n' % (str)
    self.irc.send (msg.encode(self.charset))
  
