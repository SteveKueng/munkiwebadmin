#!/bin/bash

cd $APP_DIR

if ! test "$(ls -A "/fieldkeys")"; then
  keyczart create --location=/fieldkeys --purpose=crypt
  keyczart addkey --location=/fieldkeys --status=primary --size=256
fi

if [ ! -f /secretkey ]; then
    python -c "import string,random; uni=string.ascii_letters+string.digits+string.punctuation; print repr(''.join([random.SystemRandom().choice(uni) for i in range(random.randint(45,50))]))" > /secretkey
fi

python manage.py makemigrations manifests pkgsinfo process reports updates vault
python manage.py migrate --noinput

exec "$@"