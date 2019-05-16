
var sb3_message = '';
var sb3_delete_on_missing = true;
var sb3_message_default = 'This is Scorebot v3';

var _sb3_teams = [];
var _sb3_events = [];
var _sb3_game_mode = 0;
var _sb3_message_div = null;
var _sb3_message_text = null;
var _sb3_active_effect = null;
var _sb3_active_window = null;
var _sb3_game_name_div = null;
var _sb3_team_box_max_width = null;
var _sb3_message_text_length = null;
var _sb3_team_box_max_height = null;

var _sb3_active_timers = [];

function sb3_init() {
    sb3_update_teams();
    sb3_set_message(null);
    var t = 60000;
    if (sb3_main === 1) {
        t = 15000;
    }
    _sb3_active_timers.push(setInterval(sb3_marquee, 25));
    _sb3_active_timers.push(setInterval(sb3_update_teams, t));
    _sb3_active_timers.push(setInterval(sb3_update_beacons, 50));
}
function sb3_freeze() {
    while (_sb3_active_timers.length > 0) {
        clearInterval(_sb3_active_timers.pop());
    }
}
function sb3_marquee() {
    if (_sb3_message_div === null)
        _sb3_message_div = document.getElementById('sb3_message');
    if (_sb3_message_text === null)
        _sb3_message_text = document.getElementById('sb3_message_text');
    if (_sb3_message_text_length === null) {
        var _sb3_message_canvas = document.createElement('canvas');
        var _sb3_message_canvas_context = _sb3_message_canvas.getContext('2d');
        _sb3_message_canvas_context.font = '25px Arial';
        _sb3_message_text_length = _sb3_message_canvas_context.measureText(sb3_message).width;
    }
    _sb3_message_text.innerText = sb3_message;
    var _sb3_message_offset = parseInt(_sb3_message_text.style.left.replace('px', ''));
    var _sb3_message_size = _sb3_message_div.offsetWidth;
    if (_sb3_message_offset >= _sb3_message_size) _sb3_message_offset = -1 * _sb3_message_text_length;
    else _sb3_message_offset += 2;
    _sb3_message_text.style.left = _sb3_message_offset + 'px';
}
function _sb3_team_draw() {
    var _sb3_team_div = document.getElementById('sb3_team_div_' + this.id);
    if (_sb3_game_mode === 0 && this.offense === true) {
        if (_sb3_team_div !== null) {
            _sb3_team_div.outerHTML = '';
            delete _sb3_team_div;
        }
        return;
    }
    if (_sb3_team_div === null) {
        _sb3_team_div = document.createElement('div');
        _sb3_team_div.id = 'sb3_team_div_' + this.id;
        _sb3_team_div.innerHTML = '<div class="sb3_team_info" id="sb3_team_div_info_' + this.id + '"></div>' +
            '<div class="sb3_team_health"><table><tr><td class="sb3_team_health_left" id="sb3_team_div_left_' + this.id +
            '"></td><td class="sb3_team_health_right"><table id="sb3_team_div_health_' + this.id +
            '" class="sb3_team_health_stats"></table></td></tr></table></div><div class="sb3_team_stats">' +
            '<table>' +
            '<tr>' + //<td></td>' +
            '<td class="sb3_team_status_beacons" id="sb3_team_div_status_beacons_' + this.id + '"></td>' +
            '<td class="" id="sb3_team_div_status_flags_' + this.id + '"></td>' +
            '<td class="" id="sb3_team_div_status_tickets_' + this.id + '"></td>' +
            '</tr>' +
            '<tr>' +
            '<td class="sb3_score_health" id="sb3_team_div_score_health_' + this.id + '"></td>' +
            '<td class="sb3_score_flags" id="sb3_team_div_score_flags_' + this.id + '"></td>' +
            //'<td class="sb3_score_tickets" id="sb3_team_div_score_tickets_' + this.id + '"></td>' +
            '<td class="sb3_score_beacons" id="sb3_team_div_score_beacons_' + this.id + '"></td>' +
            '</tr>' +
            '</table></div>';
        _sb3_team_div.classList.add('sb3_team');
        var _sb3_board = document.getElementById('sb3_teams');
        if (_sb3_board !== null)
            _sb3_board.appendChild(_sb3_team_div);
    }
    _sb3_team_div.style.border = '2px solid ' + this.color;
    var _sb3_team_div_pointer = document.getElementById('sb3_team_div_info_' + this.id);
    if (_sb3_team_div_pointer !== null) {
        if (this.minimal) _sb3_team_div_pointer.innerHTML = this.name;
        else _sb3_team_div_pointer.innerHTML = this.name + ': ' + this.score.total;
        if (this.offense === true) {
            _sb3_team_div_pointer.innerHTML += '<div class="sb3_team_info_off"></div>';
            _sb3_team_div.classList.add('sb3_team_off');
        }
        else _sb3_team_div.classList.remove('sb3_team_off');
    }
    _sb3_team_div_pointer = document.getElementById('sb3_team_div_left_' + this.id);
    if (_sb3_team_div_pointer !== null) {
        _sb3_team_div_pointer.style.background = this.color;
        _sb3_team_div_pointer.innerHTML = '<div class="sb3_team_logo"><img width="100" height="100" src="' +
            window.location.origin + this.logo + '"/></div>';
    }
    var _sb3_max_services = 0;
    var _sb3_host_index;
    for (_sb3_host_index = 0; _sb3_host_index < this.hosts.length; _sb3_host_index++)
        if (this.hosts[_sb3_host_index].services.length > _sb3_max_services)
            _sb3_max_services = this.hosts[_sb3_host_index].services.length;
    for (_sb3_host_index = 0; _sb3_host_index < this.hosts.length; _sb3_host_index++) {
        _sb3_team_div_pointer = document.getElementById('sb3_team_div_health_' + this.id + '_' + this.hosts[_sb3_host_index].id);
        if (_sb3_team_div_pointer === null && !this.hosts[_sb3_host_index].delete) {
            var _sb3_team_health_container = document.getElementById('sb3_team_div_health_' + this.id);
            _sb3_team_div_pointer = document.createElement('tr');
            _sb3_team_div_pointer.id = 'sb3_team_div_health_' + this.id + '_' + this.hosts[_sb3_host_index].id;
            _sb3_team_health_container.appendChild(_sb3_team_div_pointer);
        }
        else if (_sb3_team_div_pointer === null) continue;
        else if (this.hosts[_sb3_host_index].delete) {
            _sb3_team_div_pointer.outerHTML = '';
            delete _sb3_team_div_pointer;
            continue;
        }
        var _sb3_host_bonus = [], _sb3_service_index;
        for (_sb3_service_index = 0; _sb3_service_index < this.hosts[_sb3_host_index].services.length; _sb3_service_index++)
            if (this.hosts[_sb3_host_index].services[_sb3_service_index].bonus === true) _sb3_host_bonus.push(this.hosts[_sb3_host_index].services[_sb3_service_index]);
        var _sb3_host_blanks = _sb3_max_services - this.hosts[_sb3_host_index].services.length;
        if (_sb3_host_blanks < 0) _sb3_host_blanks = 0;
        var _sb3_host_health = '<td class="sb3_team_health_status_name';
        if (this.hosts[_sb3_host_index].online === false) _sb3_host_health += ' sb3_team_health_status_offline';
        _sb3_host_health += '">' + this.hosts[_sb3_host_index].name + '</td>';
        for (_sb3_service_index = 0; _sb3_service_index < this.hosts[_sb3_host_index].services.length; _sb3_service_index++)
            if (this.hosts[_sb3_host_index].services[_sb3_service_index].bonus === false) {
                _sb3_host_health += '<td class="sb3_team_health_status_' + this.hosts[_sb3_host_index].services[_sb3_service_index].status +
                    '">' + this.hosts[_sb3_host_index].services[_sb3_service_index].port;
                _sb3_host_health += this.hosts[_sb3_host_index].services[_sb3_service_index].protocol.toUpperCase() + '</td>';
            }
        var _sb3_host_empty_count;
        for (_sb3_host_empty_count = 0; _sb3_host_empty_count < _sb3_host_blanks; _sb3_host_empty_count++)
            _sb3_host_health += '<td class="sb3_team_health_status_empty"></td>';
        for (_sb3_service_index = 0; _sb3_service_index < _sb3_host_bonus.length; _sb3_service_index++) {
            _sb3_host_health += '<td class="sb3_team_health_status_bonus';
            if (_sb3_host_bonus[_sb3_service_index].status !== "")
                _sb3_host_health += ' sb3_team_health_status_' + _sb3_host_bonus[_sb3_service_index].status;
            _sb3_host_health += '">' + _sb3_host_bonus[_sb3_service_index].port;
            _sb3_host_health += _sb3_host_bonus[_sb3_service_index].protocol.toUpperCase() + '</td>';
        }
        _sb3_team_div_pointer.innerHTML = _sb3_host_health;
    }
    _sb3_team_div_pointer = document.getElementById('sb3_team_div_status_flags_' + this.id);
    if (_sb3_team_div_pointer !== null)
        if (this.offense) {
            if (this.flags.captured > 0) {
                _sb3_team_div_pointer.classList.add('sb3_team_status_flags');
                _sb3_team_div_pointer.innerHTML = '<span class="sb3_team_status_taken">' + this.flags.captured + '</span>';
                if (this.flags.lost > 0) _sb3_team_div_pointer.innerHTML = '/ ' + this.flags.lost;
            }
            else {
                if (this.flags.lost > 0) {
                    _sb3_team_div_pointer.classList.add('sb3_team_status_flags');
                    _sb3_team_div_pointer.innerHTML = this.flags.lost;
                }
                else _sb3_team_div_pointer.classList.remove('sb3_team_status_flags');
            }
        }
        else {
            if (this.flags.open > 0 || this.flags.lost > 0) {
                _sb3_team_div_pointer.innerHTML = this.flags.lost;
                _sb3_team_div_pointer.classList.add('sb3_team_status_flags');
            }
            else _sb3_team_div_pointer.classList.remove('sb3_team_status_flags');
        }
    _sb3_team_div_pointer = document.getElementById('sb3_team_div_status_tickets_' + this.id);
    if (_sb3_team_div_pointer !== null && (this.tickets.open > 0 || this.tickets.closed)) {
        _sb3_team_div_pointer.classList.add('sb3_team_status_tickets');
        _sb3_team_div_pointer.innerHTML = this.tickets.closed + ' / <span class="sb3_team_status_lost">' + this.tickets.open + '</span>';
    }
    else _sb3_team_div_pointer.classList.remove('sb3_team_status_tickets');
    for (var sb3_beacon_index = 0; sb3_beacon_index < this.beacons.length; sb3_beacon_index++)
        sb3_add_beacon(this.id, this.beacons[sb3_beacon_index].team, this.beacons[sb3_beacon_index].color);

    // Add score components
    var components = ['health', 'flags', 'beacons', 'tickets'];
    for (var i = 0; i < components.length; i++) {
        var c = components[i];
        var score_div = document.getElementById('sb3_team_div_score_' + c + '_' + this.id);
        if (score_div == null)
            continue;
        score_div.textContent = this.score[c];
    }

    /* var _sb3_team_div_style = window.getComputedStyle(_sb3_team_div);
     if (_sb3_team_box_max_width === null)
         _sb3_team_box_max_width = parseInt(_sb3_team_div_style.width.replace('px', ''));
     if (_sb3_team_box_max_width < parseInt(_sb3_team_div_style.width.replace('px', '')))
         _sb3_team_box_max_width = parseInt(_sb3_team_div_style.width.replace('px', ''));
     if (_sb3_team_box_max_height === null)
         _sb3_team_box_max_height = parseInt(_sb3_team_div_style.height.replace('px', ''));
     if (_sb3_team_box_max_height < parseInt(_sb3_team_div_style.height.replace('px', '')))
         _sb3_team_box_max_height = parseInt(_sb3_team_div_style.height.replace('px', ''));
 
     if (_sb3_team_box_max_width !== null)
         _sb3_team_div.style.width = _sb3_team_box_max_width + 'px';
     if (_sb3_team_box_max_height !== null)
         _sb3_team_div.style.height = _sb3_team_box_max_height + 'px';*/

}
function sb3_get_rgb(hex) {
    var res = hex.match(/[a-f0-9]{2}/gi);
    return res && res.length === 3 ? res.map(function (v) {return parseInt(v, 16)}) : null;
}
function sb3_update_teams() {
    var _sb3_get = new XMLHttpRequest();
    _sb3_get.onreadystatechange = function () {sb3_update_json(_sb3_get);};
    _sb3_get.open("GET", sb3_server + '/api/scoreboard/' + sb3_game + '/', true);
    _sb3_get.send(sb3_update_json);
}
function sb3_update_beacons() {
    for (var sb3_int = 0; sb3_int < _sb3_teams.length; sb3_int++) {
        var beaconDiv = document.getElementById('sb3_team_div_status_beacons_' + _sb3_teams[sb3_int].id);
        if (beaconDiv === null) continue;
        var beaconDivWidth = beaconDiv.offsetWidth, beaconDivReal = sb3_get_realWidth(beaconDiv),
            beaconDist = (beaconDivReal - beaconDivWidth);
        if (beaconDist > 25) {
            if (beaconDiv.scrollLeft > 0) {
                if (beaconDiv.scrollLeft > beaconDist) {
                    _sb3_teams[sb3_int].draw_beacon_left = true;
                    beaconDiv.scrollLeft -= 1;
                }
                else {
                    if (_sb3_teams[sb3_int].draw_beacon_left)
                        beaconDiv.scrollLeft -= 1;
                    else
                        beaconDiv.scrollLeft += 1;
                }
            }
            else {
                beaconDiv.scrollLeft += 1;
                _sb3_teams[sb3_int].draw_beacon_left = false;
            }
        }
    }
}
function sb3_add_team(team_dict) {
    if (team_dict === null) return;
    var _sb3_team_id = parseInt(team_dict['id']);
    if (_sb3_team_id !== null) {
        var _sb3_team_iter;
        for (_sb3_team_iter = 0; _sb3_team_iter < _sb3_teams.length; _sb3_team_iter++)
            if (_sb3_teams[_sb3_team_iter].id === _sb3_team_id) {
                _sb3_teams[_sb3_team_iter].update(team_dict);
                return;
            }
    }
    else return;
    team_dict.draw = _sb3_team_draw;
    team_dict.update = _sb3_team_update;
    team_dict.draw_beacon_left = false;
    _sb3_teams.push(team_dict);
    return team_dict;
}
function sb3_set_message(message) {
    if (message !== null && message.length > 0) sb3_message = message;
    else sb3_message = sb3_message_default;
    _sb3_message_text_length = null;
}
function sb3_get_realWidth(element) {
    var origWidth = element.style.maxWidth;
    var origOverflow = element.style.overflow;
    element.style.overflow = '';
    element.style.maxWidth = '';
    var realWidth = element.offsetWidth;
    element.style.overflow = origOverflow;
    element.style.maxWidth = origWidth;
    return realWidth;
}
function sb3_update_json(http_request) {
    if (http_request.readyState === 4) {
        if (http_request.status === 200) {
            var _sb3_data = http_request.responseText;
            try {
                var _sb3_json_data = JSON.parse(_sb3_data), _sb3_json_int;
                _sb3_game_mode = parseInt(_sb3_json_data.mode)
                if (_sb3_json_data.credit !== null) {
                    var _sb3_credit_div = document.getElementById('sb3_credits');
                    if (_sb3_credit_div !== null) _sb3_credit_div.innerHTML = _sb3_json_data.credit;
                }
                _sb3_events = _sb3_json_data.events;
                if (_sb3_game_name_div === null) _sb3_game_name_div = document.getElementById('sb3_game_title');
                if (_sb3_game_name_div !== null) _sb3_game_name_div.innerText = _sb3_json_data.name;
                if (_sb3_json_data.message !== null && _sb3_json_data.message.length > 0)
                    sb3_set_message(_sb3_json_data.message);
                for (_sb3_json_int = 0; _sb3_json_int < _sb3_json_data['teams'].length; _sb3_json_int++)
                    sb3_add_team(_sb3_json_data['teams'][_sb3_json_int]);
                if (sb3_delete_on_missing) {
                    var _sb3_remove_team = false, _sb3_json_int1;
                    for (_sb3_json_int = 0; _sb3_json_int < _sb3_teams.length; _sb3_json_int++) {
                        _sb3_remove_team = true;
                        for (_sb3_json_int1 = 0; _sb3_json_int1 < _sb3_json_data['teams'].length; _sb3_json_int1++)
                            if (_sb3_teams[_sb3_json_int].id === parseInt(_sb3_json_data['teams'][_sb3_json_int1].id)) {
                                _sb3_remove_team = false;
                                break;
                            }
                        if (_sb3_remove_team) {
                            var _sb3_team_div = document.getElementById('sb3_team_div_' + _sb3_teams[_sb3_json_int].id);
                            _sb3_team_div.outerHTML = '';
                            delete _sb3_team_div;
                            delete _sb3_teams[_sb3_json_int];
                        }
                    }
                    var _sb3_teams1 = [];
                    for (_sb3_json_int = 0; _sb3_json_int < _sb3_teams.length; _sb3_json_int++) {
                        if (_sb3_teams[_sb3_json_int] !== null)
                            _sb3_teams1.push(_sb3_teams[_sb3_json_int]);
                    }
                    _sb3_teams = _sb3_teams1;
                }
                for (_sb3_json_int = 0; _sb3_json_int < _sb3_teams.length; _sb3_json_int++)
                    _sb3_teams[_sb3_json_int].draw();
                for (_sb3_json_int = 0; _sb3_json_int < _sb3_teams.length; _sb3_json_int++);

            }
            catch (exception) {
                console.error('Exception occurred! ' + exception)
            }
        }
        else {
            console.error('Scoreboard returned ' + http_request.status + ' when attempting to update!');
            console.error(http_request.responseText);

        }
    }
}
function _sb3_team_update(team_update) {
    this.name = team_update['name'];
    this.logo = team_update['logo'];
    this.color = team_update['color'];
    this.offense = team_update['offense'];
    var team_old_beacons = this.beacons;
    this.beacons = team_update['beacons'];
    this.minimal = team_update['minimal'];
    for (var sb3_beacon_index = 0; sb3_beacon_index < team_old_beacons.length; sb3_beacon_index++) {
        var team_beacon_exists = false;
        for (var sb3_beacon_index1 = 0; sb3_beacon_index1 < this.beacons; sb3_beacon_index1++)
            if (team_old_beacons[sb3_beacon_index].team === this.beacons[sb3_beacon_index1]) {
                team_old_beacons = true;
                break;
            }
        if (!team_beacon_exists) sb3_delete_beacon(this.id, team_old_beacons[sb3_beacon_index].team);
    }
    this.compromises = parseInt(team_update['compromises']);
    this.flags['open'] = parseInt(team_update['flags']['open']);
    this.flags['lost'] = parseInt(team_update['flags']['lost']);
    this.score['total'] = parseInt(team_update['score']['total']);
    this.score['health'] = parseInt(team_update['score']['health']);
    this.score['beacons'] = parseInt(team_update['score']['beacons']);
    this.score['flags'] = parseInt(team_update['score']['flags']);
    this.score['tickets'] = parseInt(team_update['score']['tickets']);
    this.tickets['open'] = parseInt(team_update['tickets']['open']);
    this.flags['captured'] = parseInt(team_update['flags']['captured']);
    this.tickets['closed'] = parseInt(team_update['tickets']['closed']);
    var team_host_int, team_service_int;
    for (team_host_int = 0; team_host_int < team_update['hosts'].length; team_host_int++) {
        var team_host_ins = null, _sb3_host_inc;
        for (_sb3_host_inc = 0; _sb3_host_inc < this.hosts.length; _sb3_host_inc++)
            if (parseInt(this.hosts[_sb3_host_inc].id) === parseInt(team_update['hosts'][team_host_int].id)) {
                team_host_ins = this.hosts[_sb3_host_inc];
                break;
            }
        if (team_host_ins === null) {
            team_host_ins = {};
            team_host_ins.services = [];
            this.hosts.push(team_host_ins);
        }
        team_host_ins.delete = false;
        team_host_ins.name = team_update['hosts'][team_host_int]['name'];
        team_host_ins.id = parseInt(team_update['hosts'][team_host_int].id);
        team_host_ins.online = team_update['hosts'][team_host_int]['online'];
        for (team_service_int = 0; team_service_int < team_update['hosts'][team_host_int]['services'].length; team_service_int++) {
            var team_service_ins = null, _sb3_service_inc;
            if (team_host_ins.services.length > 0)
                for (_sb3_service_inc = 0; _sb3_service_inc < team_host_ins.services.length; _sb3_service_inc++)
                    if (parseInt(team_host_ins.services[_sb3_service_inc].id) === parseInt(team_update['hosts'][team_host_int]['services'][team_service_int].id)) {
                        team_service_ins = team_host_ins.services[_sb3_service_inc];
                        break;
                    }
            if (team_service_ins === null) {
                team_service_ins = {};
                team_host_ins.services.push(team_service_ins);
            }
            team_service_ins.id = parseInt(team_update['hosts'][team_host_int]['services'][team_service_int].id);
            team_service_ins.bonus = team_update['hosts'][team_host_int]['services'][team_service_int]['bonus'];
            team_service_ins.status = team_update['hosts'][team_host_int]['services'][team_service_int]['status'];
            team_service_ins.protocol = team_update['hosts'][team_host_int]['services'][team_service_int]['protocol'];
            team_service_ins.port = parseInt(team_update['hosts'][team_host_int]['services'][team_service_int]['port']);
        }
    }
    if (sb3_delete_on_missing) {
        var _sb3_host_inc, _sb3_host_inc1, _sb3_host_mark;
        for (_sb3_host_inc = 0; _sb3_host_inc < this.hosts.length; _sb3_host_inc++) {
            _sb3_host_mark = true;
            for (_sb3_host_inc1 = 0; _sb3_host_inc1 < team_update['hosts'].length; _sb3_host_inc1++)
                if (this.hosts[_sb3_host_inc].id === parseInt(team_update['hosts'][_sb3_host_inc1].id)) {
                    _sb3_host_mark = false;
                    break;
                }
            if (_sb3_host_mark)
                this.hosts[_sb3_host_inc].delete = true;
        }
    }
}
function sb3_delete_beacon(team_id, beacon_team_id) {
    var beaconDiv = document.getElementById('sb3_team_div_beacon_' + team_id + '_' + beacon_team_id);
    if (beaconDiv !== null) beaconDiv.outerHTML = '';
}
function sb3_add_beacon(team_id, beacon_team_id, beacon_color) {
    var beaconDiv = document.getElementById('sb3_team_div_status_beacons_' + team_id);
    var beaconTestDiv = document.getElementById('sb3_team_div_beacon_' + team_id + '_' + beacon_team_id);
    if (beaconDiv === null) return;
    if (beaconTestDiv !== null) return;
    var beaconColor = sb3_get_rgb(beacon_color);
    var beaconLogo = new Image();
    beaconLogo.onload = function () {
        var beaconCanvas = document.createElement("canvas");
        beaconCanvas.width = 25;
        beaconCanvas.height = 25;
        var beaconImage = document.createElement("img");
        beaconImage.width = 25;
        beaconImage.height = 25;
        beaconImage.id = 'sb3_team_div_beacon_' + team_id + '_' + beacon_team_id;
        var beaconDraw = beaconCanvas.getContext("2d");
        beaconDraw.drawImage(beaconLogo, 0, 0);
        var beaconCanvasImg = beaconDraw.getImageData(0, 0, 128, 128);
        for (var beaconInt = 0; beaconInt < beaconCanvasImg.data.length; beaconInt += 4) {
            beaconCanvasImg.data[beaconInt] = beaconColor[0];
            beaconCanvasImg.data[beaconInt + 1] = beaconColor[1];
            beaconCanvasImg.data[beaconInt + 2] = beaconColor[2];
        }
        beaconDraw.putImageData(beaconCanvasImg, 0, 0);
        beaconImage.src = beaconCanvas.toDataURL("image/png");
        beaconDiv.append(beaconImage)
    };
    beaconLogo.src = sb3_server + '/static/img/beacon.png';
}


function sb3_draw_event() {
    if (_sb3_active_effect !== null) {
        if (_sb3_active_effect.timeout === 0) {
            var _sb3_effect_div = document.getElementById('sb3_events_effects');
            _sb3_effect_div.innerHTML = '';
        }
    }
    if (_sb3_active_window !== null) {
        if (_sb3_active_window.timeout === 0) {
            var _sb3_window_div = document.getElementById('sb3_events_windows');
            _sb3_window_div.innerHTML = '';
        }
    }
    for (var sb3_event_int = 0; sb3_event_int < _sb3_events.length; sb3_event_int++) {
        if (_sb3_events[sb3_event_int].type === 'message') {
            var _sb3_message_div = document.getElementById('sb3_messages');
            _sb3_message_div.innerHTML += '<div class="sb3_event_message">' + _sb3_events[sb3_event_int].data.message + '</div>';
        }
    }
}

