function L() {
   if (window.console && window.console.log)
     console.log.apply(console, arguments);
}


$.fn.extend({
	showLightbox: function() {
		return this
			.css('opacity', 0)
			.addClass('visible')
			.fadeTo(500, 1);
	},

	hideLightbox: function() {
		return this
			.fadeTo(500, 0, function() {
				$(this).removeClass('visible');
			});
	},

	escape: function(f) {
		return this.keypress(function(e) {
			if (e.keyCode == 27) {
				return f.apply(this, [ e ]);
			}
		});
	}
});

function _notifications() {
  // Initially, hide them all
  hideAllMessages();

  // Show message
  for (var i = 0; i < myMessages.length; i++) {
    $('.'+myMessages[i]).animate({top:"0"}, 500);
  }

  // When message is clicked, hide it
  $('.message').click(function(){
    $(this).animate({top: -$(this).outerHeight()}, 500);
  });
  setTimeout(function() {
    $('.message').each(function(){
      $(this).animate({top: -$(this).outerHeight()}, 500);
    });
  }, 5 * 1000);
}

$(document).ready( function() {
  _notifications();

  $('select[name="cal_month"]').change(function() {
    $(this).parents('form').submit();
  });

	$([
		{ klass: 'swap-offer', box: 'swapoffer-lightbox'  },
		{ klass: 'swap-req', box: 'swapreq-lightbox'  },
		{ klass: 'volunteer', box: 'volunteer-lightbox'  },
		{ klass: 'back-out', box: 'backout-lightbox'  },
	]).each(function (_, i) {
		var selectBox = '#' + i.box;
    var selectLinks = 'a.' + i.klass;

		$(selectLinks).click( function() {
      var pk = $(this).data('pk');
			var onEscape = function (e) {
				if (e.keyCode == 27) {
					return doHide();
				}
			};

			var onSubmit = function() {
        return true;
			};

			var doHide = function() {
				$(document).unbind('keypress', onEscape);
				$(document).unbind('submit', onSubmit);
				$(selectBox).hideLightbox();
				return false;
			};

			$(document).keypress(onEscape);
			$(selectBox+' form').submit(onSubmit);
			$(selectBox+' .cancel').click(doHide);

      $.getJSON('/roster/info.json', {pk: pk}, function(response) {
        if (!response) {
          alert('Invalid roster item clicked');
          return;
        }
        $('.date', selectBox).text(response.date);
        $('.sheriff', selectBox).text(response.name);
        $('form input[name="pk"]', selectBox).val(response.pk);
        $(selectBox).showLightbox();
        $( $(selectBox+' input').get(0) ).focus();
      });

			return false;
		});

		$(document).escape( function() {
			$(selectBox).hideLightbox()
		});
	});
});
