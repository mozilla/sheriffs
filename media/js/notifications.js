/* http://www.red-team-design.com/cool-notification-messages-with-css3-jquery */
var myMessages = ['info', 'warning', 'error', 'success'];
function hideAllMessages() {
  // this array will store height for each
  var messagesHeights = new Array();
  for (i = 0; i < myMessages.length; i++) {
    // fill array
    messagesHeights[i] = $('.' + myMessages[i]).outerHeight();
    //move element outside viewport
    $('.' + myMessages[i]).css('top', -messagesHeights[i]);
  }
}

function showMessage(type) {
  $('.' + type + '-trigger').click(function() {
    hideAllMessages();
    $('.' + type).animate({top: '0'}, 500);
  });
}
