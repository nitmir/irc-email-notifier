install:
	install -g root -o root -m 0755 notifier.py /usr/local/bin/notifier
	install -g root -o root -m 0755 notifier.init /etc/init.d/notifier
	install -d -g root -o root -m 0755 /etc/notifier
	install -g root -o root -m 0644 sample.conf.example /etc/notifier/sample.conf.example

unintall:
	rm /usr/local/bin/notifier
