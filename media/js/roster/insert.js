
$(function() {
  //var textarea = $('textarea');
  var current = $('#id_username');
  $('#available-users a').click(function() {
    $('#available-users a').fadeTo(0, 1.0);
    var username = $(this).attr('id');
    if (current.val() != username) {
      // add to textarea
      current.val(username);
      $(this).fadeTo(0, 0.3);
    } else {
      current.val('');
      $(this).fadeTo(0, 1.0);
    }
    return false;
  });
});
