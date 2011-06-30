/* http://www.red-team-design.com/cool-notification-messages-with-css3-jquery */
var myMessages = ['info','warning','error','success'];
function hideAllMessages()
{
                 var messagesHeights = new Array(); // this array will store height for each

                 for (i=0; i<myMessages.length; i++)
                 {
                                  messagesHeights[i] = $('.' + myMessages[i]).outerHeight(); // fill array
                                  $('.' + myMessages[i]).css('top', -messagesHeights[i]); //move element outside viewport
                 }
}

function showMessage(type)
{
        $('.'+ type +'-trigger').click(function(){
                  hideAllMessages();
                  $('.'+type).animate({top:"0"}, 500);
        });
}
