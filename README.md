#notifier

### What this is

This is a IRC bot written in python that notify IRC channel or users of new        
mails in an IMAP mailddir.

### Dependancy

```$ sudo pip install imaplib2```

(the last version of imaplib2 is avaiable at [http://imaplib2.sourceforge.net/](http://imaplib2.sourceforge.net/))

### Installation

```# make install```

### Usage

If you installed the program via the Makefile,
 put config files (usually botname.conf) in ```/etc/notifier```, one by bot 
(see the sample config file in the directory) and run :
 
 ```$ sudo service notifier start```
 
 Otherwise or for debugging purpose juste run :
 
 ```$ ./notifier.py --confdir /path/to/config/dir file.conf```
