install:
	mkdir -p /usr/local/bin/notifier/
	cp notifier.py /usr/local/bin/notifier/
	cp imaplib2.py /usr/local/bin/notifier/
	cp notifier.init /etc/init.d/
	mkdir -p /etc/notifier/
	cp sample.conf.example /etc/notifier/

unintall:
	rm /usr/local/bin/notifier/notifier.py
	rm /usr/local/bin/notifier/imaplib2.py
	rmdir /usr/local/bin/notifier/
