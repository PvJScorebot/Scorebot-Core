#!/usr/bin/bash
# Usage setup.sh <scorebotdir>
#
# Copyright (C) 2020 iDigitalFlame
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

# Change these global vars to suit your needes (if needed)
SBEURL="https://github.com/iDigitalFlame/scorebot-core.git"
# The scorebot-core branch to switch to, if empty, this will keep it as master.
SBEBRANCH=""

setup_sbe() {
    if [ $# -ne 1 ]; then
        printf "$0 <path>\n"
        return 1
    fi
    SBEDIR="$1"
    mkdir -p "$SBEDIR" 2> /dev/null
    if  [ $? -ne 0 ]; then
        printf "Could not create directory \"$SBEDIR\"!\n"
        exit 1
    fi
    bin_git=$(whereis git | awk '{print $2}')
    bin_venv=$(whereis virtualenv | awk '{print $2}')
    if [ -z "$bin_git" ]; then
        printf "We are missing the \"git\" binary, you will be prompted to install it now..\n"
        setup_sbe_pkg "git"
    fi
    if [ -z "$bin_venv" ]; then
        printf "We are missing the \"virtualenv\" binary, you will be prompted to install it now..\n"
        setup_sbe_pkg "python-virtualenv"
    fi
    printf "Creating virutal enviorment..\n"
    $bin_venv --always-copy "$SBEDIR/python"
    ret=$?
    if [ $ret -ne 0 ]; then
        printf "Virtualenv failed with a status of \"$ret\"!\n"
        exit 1
    fi
    printf "Downloading scorebot-core..\n"
    git clone $SBEURL "$SBEDIR/scorebot"
    ret=$?
    if [ $ret -ne 0 ]; then
        printf "Git failed with a status of \"$ret\"!\n"
        exit 1
    fi
    cd "$SBEDIR/scorebot"
    if ! [ -z "$SBEBRANCH" ]; then
        printf "Switching to branch \"$SBEBRANCH\"..\n"
        git checkout $SBEBRANCH 1> /dev/null
    fi
    mkdir "scorebot_data"
    printf "Installing python deps in venv..\n"
    bash -c "source \"$SBEDIR/python/bin/activate\"; cd \"$SBEDIR/scorebot\"; unset PIP_USER; pip install -r requirements.txt; exit \$?"
    ret=$?
    if [ $ret -ne 0 ]; then
        printf "Deps install via PIP failed with a status of \"$ret\"!\n"
        exit 1
    fi
    bash -c "source \"$SBEDIR/python/bin/activate\"; cd \"$SBEDIR/scorebot\"; env SBE_SQLLITE=1 python manage.py makemigrations scorebot_grid scorebot_core scorebot_game; exit \$?"
    ret=$?
    if [ $ret -ne 0 ]; then
        printf "manage.py failed with a status of \"$ret\"!\n"
        exit 1
    fi
    bash -c "source \"$SBEDIR/python/bin/activate\"; cd \"$SBEDIR/scorebot\"; env SBE_SQLLITE=1 python manage.py migrate; exit \$?"
    ret=$?
    if [ $ret -ne 0 ]; then
        printf "manage.py failed with a status of \"$ret\"!\n"
        exit 1
    fi
    printf "Created superuser \"root\" with password \"password\"..\n"
    bash -c "source \"$SBEDIR/python/bin/activate\"; cd \"$SBEDIR/scorebot\"; env SBE_SQLLITE=1 python manage.py shell -c \"from django.contrib.auth.models import User; User.objects.create_superuser('root', '', 'password')\"; exit $?"
    ret=$?
    if [ $ret -ne 0 ]; then
        printf "manage.py failed with a status of \"$ret\"!\n"
        exit 1
    fi
    printf "Scorebot setup complete, give me a sec, creating support files...\n"
    printf '#!/usr/bin/bash\n\nSBEDIR="' > "$SBEDIR/scorebot/start-daemon.sh"
    printf "$SBEDIR" >>  "$SBEDIR/scorebot/start-daemon.sh"
    printf '"\nSBEPYTHON="$SBEDIR/python"\n\nbash -c "source \"$SBEPYTHON/bin/activate\"; env SBE_SQLLITE=1 python \"$SBEDIR/scorebot/daemon.py\""\n' >>  "$SBEDIR/scorebot/start-daemon.sh"
    printf '#!/usr/bin/bash\n\nSBEDIR="' >  "$SBEDIR/scorebot/start-server.sh"
    printf "$SBEDIR" >>  "$SBEDIR/scorebot/start-server.sh"
    printf '"\nSBEPYTHON="$SBEDIR/python"\n\nbash -c "source \"$SBEPYTHON/bin/activate\"; env SBE_SQLLITE=1 python \"$SBEDIR/scorebot/manage.py\" runserver"\n' >>  "$SBEDIR/scorebot/start-server.sh"
    printf '#!/usr/bin/bash\n\n' > "$SBEDIR/scorebot/start-background.sh"
    printf "screen -dmS sbe3-daemon bash $SBEDIR/scorebot/start-daemon.sh\nscreen -dmS sbe3-web bash $SBEDIR/scorebot/start-server.sh\n" >> "$SBEDIR/scorebot/start-background.sh"
    printf 'printf "Both SBE services started, you can access the server at http://localhost:8000/\\n"\n' >> "$SBEDIR/scorebot/start-background.sh"
    chmod 755 start-*.sh
    printf "Done!\nOnce started, admin page my be accesed at \"http://localhost:8000/admin/\"\n"
    return 0
}

setup_sbe_pkg() {
    if [ $# -ne 1 ]; then
        return 1
    fi
    if [ -z "$(whereis pacman | awk '{print $2}')" ]; then
        printf "I don't understand your distro, please use your local package manager to install \"$1\", then re-run this script.\n"
        exit 1
    fi
    if [ $UID -ne 0 ]; then
        printf "I see that you are not running as root that's fine, sudo will be used once.\n"
        bin_sudo=$(whereis sudo | awk '{print $2}')
        if [ -z "$bin_sudo" ]; then
            printf "Package \"sudo\" is not installed, please install it and re-run this script.\n"
            exit 1
        fi
        $bin_sudo pacman -S $1
        ret=$?
    else
        pacman -S $1
        ret=$?
    fi
    if [ $ret -ne 0 ]; then
        printf "Pacman returned a non-zero error code \"$ret\"!\n"
        exit 1
    fi
    return 0
}

if [ $# -lt 1 ]; then
    printf "$0 <scorebotdir>\n"
    exit 1
fi

setup_sbe "$1"
exit $?
