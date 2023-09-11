(function () {
    var url = new URL(window.location.href);
    var session_id = url.pathname.match('([0-9])*$')[0];
    var $cards = $('.card');
    var upgrade_from_id;
    $cards.find('a').on('click', function (event) {
        event.preventDefault();
        //alert('click');
        var $card = $(this).closest('.card');
        var card_id = $card.data('card-id');
        var action = $(this).data('action');
        if (action == 'upgrade') {
            upgrade_from_id = card_id;
            return;
        }
        $.post('/game/api/' + session_id, {
            action: action,
            card_id: card_id,
            upgrade_from: upgrade_from_id
        })
            .done(function (data) {
                if (data['error']) {
                    alert(data['error']);
                } else {
                    location.reload();
                }
            })
            .fail(function (data) {
                alert("Something went wrong");
            })
    });

    $('#pass-btn').on('click', function () {
        $.post('/game/api/' + session_id, {
            action: 'pass'
        })
            .done(function (data) {
                if (data['error']) {
                    alert(data['error']);
                } else {
                    location.reload();
                }
            })
            .fail(function (data) {
                alert("Something went wrong.");
            })
    });
})();