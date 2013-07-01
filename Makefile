install:
	mkdir -p /usr/local/bin/notifier/
	cp notifier.py imaplib2.py /usr/local/bin/notifier/
	cp notifier.init /etc/init.d/notifier
	mkdir -p /etc/notifier/
	cp sample.conf.example /etc/notifier/
	chmod 755 /usr/local/bin/notifier/notifier.py /etc/init.d/notifier

unintall:
	rm /usr/local/bin/notifier/notifier.py /usr/local/bin/notifier/imaplib2.py
	rmdir /usr/local/bin/notifier/
