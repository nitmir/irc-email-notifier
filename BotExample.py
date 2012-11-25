#!/usr/bin/env python
# -*- coding: utf-8 -*-
import socket,time,imaplib2
import notifier


# adresse du serveur irc
network = 'irc.example.net'

# port du serveur irc
port = 6667

# encodage des messages que le bot utilisera pour envoyer des messages sur irc
charset='utf-8'

# Liste des chan à notifier des arrivée de mail
chan=["#channel"]

# Liste de nicks à notifier
notice=["nick1","nick2"]

# Nom du bot sur irc
nick="NickName"

# temps au bout duquel s'il n'y a aucune activité vers le serveur irc, le bot quitte. 
# À savoir que la plupart des serveurs irc explusent les clients qu'il n'y a aucune activité 
# (par de ping, pong, au quoique se soit d'autre) au bout de 180s.
# Devrait être deux ou trois fois la durée de timeout du serveur irc.
irc_timeout=360.0

# adresse du serveur imap
host='imap.example.net'

# utiliser ssl pour chiffrer la comunication avec le serveur mail 
# le serveur doit le supporter
# use_ssl=False
use_ssl=True

# nom d'utilisateur mail
user='mail_username'
# mot de passe mail
password='mail_password'
# dossier depuis lequel on notifie les mails
box='INBOX'

# niveau de verbosité du script
debug=0

# Format de la notification : liste de header mail et de masque à appliquer au contenue du header por l'affichier.
# headers=[['subject','%s']]
# headers=[['from','Mail de %s '],['to','à %s.']]
headers=[['from','Mail de %s : '],['subject','%s']]


notifier.Notifier(
	network, 
	chan, 
	nick, 
	host, 
	user, 
	password,  
	box, 
	port=port, 
	debug=0, 
	headers=headers, 
	irc_timeout=irc_timeout,
	notice=notice,
	charset=charset,
	use_ssl=use_ssl
)

