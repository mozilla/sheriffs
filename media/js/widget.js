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

// Mozilla Sheriffs Duty Widget
var Sheriffs_Widget_Version = '1.0';
var Sheriffs_Host_Name = 'sheriffs';

var Sheriffs = (function() {
  var _options = typeof sheriff_options != 'undefined' ? sheriff_options : {};
  var LIMIT = _options.limit || 5;
  var USE_DATE_LABELS = _options.use_date_labels || false;
  var HOST_NAME = _options.host_name || Sheriffs_Host_Name; // HARD CODED!
  var BASE_URL = ('https:' == document.location.protocol ? 'https://' : 'http://') + HOST_NAME;
  var CONTENT_URL = BASE_URL + '/api/v1/slot/?format=jsonp&callback=Sheriffs.callback&limit=' + LIMIT;
  var ROOT = _options.root_node_id || 'sheriffs_widget';
  var ROOT_CSS = _options.root_css || '';
  var CSS = '#sheriffs_widget td { padding-right:15px; }#sheriffs_widget .foot { font-size:10px;';

  function insertStylesheet() {
    var style = document.createElement('style');
    style.appendChild(document.createTextNode(CSS));
    document.getElementsByTagName('head')[0].appendChild(style);
  }
  function requestContent() {
    var s = document.createElement('script');
    s.type = 'text/javascript';
    s.defer = true;
    s.src = CONTENT_URL;
    document.getElementsByTagName('head')[0].appendChild(s);
  }
  document.write('<div id="' + ROOT + '" style="display:none"></div>');
  insertStylesheet();
  requestContent();
  return {
     callback: function(response) {
       if (!response) return;
       var div = document.getElementById(ROOT);
       var tr, td, date, table = document.createElement('table');
       var prev_date;
       for (var i = 0; i < response.objects.length; i++) {
         tr = document.createElement('tr');
         td = document.createElement('td');
         if (USE_DATE_LABELS && response.objects[i].date_label)
           date = document.createTextNode(response.objects[i].date_label);
         else
           date = document.createTextNode(response.objects[i].date);
         td.appendChild(date);
         tr.appendChild(td);
         td = document.createElement('td');
         if (response.objects[i].email) {
           a = document.createElement('a');
           a.href = 'mailto:' + response.objects[i].email;
           a.appendChild(document.createTextNode(response.objects[i].user));
           td.appendChild(a);
         } else {
           td.appendChild(document.createTextNode(response.objects[i].user));
         }
         tr.appendChild(td);
         table.appendChild(tr);
       }
       div.appendChild(table);
       // consider making this a link
       var foot = document.createElement('a');
       foot.setAttribute('class', 'foot');
       foot.setAttribute('href', BASE_URL);
       foot.setAttribute('title', 'Widget version ' + Sheriffs_Widget_Version);
       foot.appendChild(document.createTextNode('Mozilla Sheriffs Duty'));
       div.appendChild(foot);
       div.style.display = 'block';
     }
  };
})();
