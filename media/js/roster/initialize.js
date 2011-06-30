
$(function() {
  var textarea = $('textarea');
  $('#available-users a').click(function() {
    var id= $(this).attr('id');
    if (-1 == textarea.val().search(id + '\n')) {
      // add to textarea
      textarea.val(textarea.val() + id + '\n');
      $(this).fadeTo(0, 0.3);
    } else {
      textarea.val(textarea.val().replace(id + '\n', ''))
      $(this).fadeTo(0, 1.0);
    }
    return false;
  });
});
