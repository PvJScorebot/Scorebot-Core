#!/usr/bin/bash
#
# Usage setup.sh <scorebotdir>
#

if [ $# -lt 2 ]; then
    printf "$0 <scorebotdir>\n"
    exit 1
fi

SBEDIR="$1"

if [ ! -d "$SBEDIR" ]; then
    mkdir -p "$SBEDIR" 2> /dev/null
    if  [ $? -ne 0 ]; then
        printf "Could not create directory \"$SBEDIR\"!\n"
        exit 1
    fi
fi

printf "The next commands use sudo..\n"

sudo pacman -Syy
sudo pacman -S python-virtualenv git python python-pip mariadb-clients screen
if [ $? -ne 0 ]; then
    printf "Pacman failed with a status of \"$?\"!\n"
    exit 1
fi

virtualenv --always-copy "$SBEDIR/python"
if [ $? -ne 0 ]; then
    printf "Virtualenv failed with a status of \"$?\"!\n"
    exit 1
fi

git clone "https://github.com/iDigitalFlame/scorebot-core.git" "$SBEDIR/scorebot3"
if [ $? -ne 0 ]; then
    printf "Git failed with a status of \"$?\"!\n"
    exit 1
fi

cd "$SBEDIR/scorebot3"

# Change to target a different build
git checkout v3.3-atomic

source "$SBEDIR/python/bin/activate"
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    printf "Pip failed with a status of \"$?\"!\n"
    exit 1
fi

python manage.py makemigrations scorebot_grid scorebot_core scorebot_game
if [ $? -ne 0 ]; then
    printf "manage.py failed with a status of \"$?\"!\n"
    exit 1
fi

python manage.py migrate
if [ $? -ne 0 ]; then
    printf "manage.py failed with a status of \"$?\"!\n"
    exit 1
fi

printf "Create a password for django, username is \"root\".."
python manage.py createsuperuser --username root --email ""
if [ $? -ne 0 ]; then
    printf "manage.py failed with a status of \"$?\"!\n"
    exit 1
fi

printf "Scorebot setup complete, give me a sec, creating support files...\n"
printf '#!/usr/bin/bash\n\nSBEDIR="' > "$SBEDIR/scorebot3/start-daemon.sh"
printf "$SBEDIR" >>  "$SBEDIR/scorebot3/start-daemon.sh"
printf '"\nSBEPYTHON="$SBEDIR/python"\n\nsource "$SBEPYTHON/bin/activate"\n\npython "$SBEDIR/scorebot3/daemon.py"\n' >>  "$SBEDIR/scorebot3/start-daemon.sh"
printf '#!/usr/bin/bash\n\nSBEDIR="' >  "$SBEDIR/scorebot3/start-server.sh"
printf "$SBEDIR" >>  "$SBEDIR/scorebot3/start-server.sh"
printf '"\nSBEPYTHON="$SBEDIR/python"\n\nsource "$SBEPYTHON/bin/activate"\n\npython "$SBEDIR/scorebot3/manage.py" runserver\n' >>  "$SBEDIR/scorebot3/start-server.sh"
printf '#!/usr/bin/bash\n\nSBEDIR="' >  "$SBEDIR/scorebot3/start-background.sh"
printf "$SBEDIR" >>  "$SBEDIR/scorebot3/start-background.sh"
printf '"\nscreen -dmS sbe3-daemon "$SBEDIR/scorebot3/start-daemon.sh\nscreen -dmS sbe3-web "$SBEDIR/scorebot3/start-server.sh\n' > "$SBEDIR/scorebot3/start-background.sh"

printf "Done!\n"
