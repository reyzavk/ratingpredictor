import { Template } from 'meteor/templating';
import { ReactiveVar } from 'meteor/reactive-var';
import $ from 'jquery';

import './main.html';

import 'bootstrap'
import 'bootstrap/dist/css/bootstrap.css';
import 'bootstrap/dist/css/bootstrap-theme.css';

if('WebSocket' in window){
    console.log('websocket supported !!');
}

var socket = new WebSocket('ws://localhost:8000/comm/');

function refresh_ignore(){
    var message = {'action': 'query word'}
    socket.send(JSON.stringify(message))

}

function refresh_unignore(){
    var message = {'action': 'query ignore'}
    socket.send(JSON.stringify(message))

}

socket.onopen = function open() {
    refresh_ignore();
    refresh_unignore();
    console.log('WebSockets connection created.');
};

Template.body.events({
    'submit form#scrape': function(e){
        e.preventDefault();
        var url = $('#scrape').find('input[name="scrape-link"]').val();
        var message = {'action': 'scrape', 'url': url};
        socket.send(JSON.stringify(message));
    }
})

Template.body.events({
    'submit form#ignore': function(e){
        e.preventDefault();
        var word = $('#ignore select').val();
        var message = {'action': 'ignore', 'word': word};
        socket.send(JSON.stringify(message));
        $('#ignore-msg').text("kata [" + word + "] berhasil di blacklist");
    }
})

Template.body.events({
    'submit form#unignore': function(e){
        e.preventDefault();
        var word = $('#unignore select').val();
        var message = {'action': 'unignore', 'word': word};
        socket.send(JSON.stringify(message));
        $('#unignore-msg').text("kata [" + word + "] berhasil di whitelist");
    }
})

Template.body.events({
    'submit form#predict': function(e){
        e.preventDefault();
        var sentence = $('#predict').find('input[name="predict-sentence"]').val();
        var message = {'action': 'predict', 'sentence': sentence};
        socket.send(JSON.stringify(message));
    }
})

socket.onmessage = function consumer(message){
    data = JSON.parse(message.data)
    console.log(data)
    if(data['action'] == 'query word'){
        var $select = $('#ignore select');
        $select.empty();
        $.each(data['words'], function(i, item){
            $select.append($(new Option(item, item)));
        });
    }else if(data['action'] == 'query ignore'){
        var $select = $('#unignore select');
        $select.empty();
        $.each(data['words'], function(i, item){
            $select.append($(new Option(item, item)));
        });
    }else if(data['action'] == 'predict'){
        $('#prediction').text('prediksi bintang/rating : ' + data['prediction']);
    }else{
        refresh_ignore();
        refresh_unignore();
    }
}
