#!/bin/sh

if [ -z "$PGP_KEYSERVER" ]; 
then 
    gpg  --keyserver keys.gnupg.net --recv-keys $YOUR_PGP_KEY_ID
else
    gpg  --keyserver "$PGP_KEYSERVER" --recv-keys $YOUR_PGP_KEY_ID
fi
