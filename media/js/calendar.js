/* ***** BEGIN LICENSE BLOCK *****
 * Version: MPL 1.1/GPL 2.0/LGPL 2.1
 * 
 * The contents of this file are subject to the Mozilla Public License Version
 * 1.1 (the "License"); you may not use this file except in compliance with
 * the License. You may obtain a copy of the License at
 * http://www.mozilla.org/MPL/
 * 
 * Software distributed under the License is distributed on an "AS IS" basis,
 * WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
 * for the specific language governing rights and limitations under the
 * License.
 * 
 * The Original Code is Mozilla Sheriff Duty.
 * 
 * The Initial Developer of the Original Code is Mozilla Corporation.
 * Portions created by the Initial Developer are Copyright (C) 2011
 * the Initial Developer. All Rights Reserved.
 * 
 * Contributor(s):
 * 
 * Alternatively, the contents of this file may be used under the terms of
 * either the GNU General Public License Version 2 or later (the "GPL"), or
 * the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
 * in which case the provisions of the GPL or the LGPL are applicable instead
 * of those above. If you wish to allow use of your version of this file only
 * under the terms of either the GPL or the LGPL, and not to allow others to
 * use your version of this file under the terms of the MPL, indicate your
 * decision by deleting the provisions above and replace them with the notice
 * and other provisions required by the GPL or the LGPL. If you do not delete
 * the provisions above, a recipient may use your version of this file under
 * the terms of any one of the MPL, the GPL or the LGPL.
 * 
 * ***** END LICENSE BLOCK ***** */

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
        return f.apply(this, [e]);
      }
    });
  }
});

function _notifications() {
  // Initially, hide them all
  hideAllMessages();

  // Show message
  for (var i = 0; i < myMessages.length; i++) {
    $('.' + myMessages[i]).animate({top: '0'}, 500);
  }

  // When message is clicked, hide it
  $('.message').click(function() {
    $(this).animate({top: -$(this).outerHeight()}, 500);
  });
  setTimeout(function() {
    $('.message').each(function() {
      $(this).animate({top: -$(this).outerHeight()}, 500);
    });
  }, 5 * 1000);
}

$(document).ready(function() {
  _notifications();

  $('select[name="cal_month"]').change(function() {
    $(this).parents('form').submit();
  });

  $([
    { klass: 'swap-offer', box: 'swapoffer-lightbox' },
    { klass: 'swap-req', box: 'swapreq-lightbox' },
    { klass: 'volunteer', box: 'volunteer-lightbox' },
    { klass: 'back-out', box: 'backout-lightbox' }
  ]).each(function(_, i) {
    var selectBox = '#' + i.box;
    var selectLinks = 'a.' + i.klass;

    $(selectLinks).click(function() {
      var pk = $(this).data('pk');
      var onEscape = function(e) {
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
      $(selectBox + ' form').submit(onSubmit);
      $(selectBox + ' .cancel').click(doHide);

      $.getJSON('/roster/info.json', {pk: pk}, function(response) {
        if (!response) {
          alert('Invalid roster item clicked');
          return;
        }
        $('.date', selectBox).text(response.date);
        $('.sheriff', selectBox).text(response.name);
        $('form input[name="pk"]', selectBox).val(response.pk);
        $(selectBox).showLightbox();
        $($(selectBox + ' input').get(0)).focus();
      });

      return false;
    });

    $(document).escape(function() {
      $(selectBox).hideLightbox();
    });
  });
});
