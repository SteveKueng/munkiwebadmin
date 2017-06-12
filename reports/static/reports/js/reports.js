//global var
var imagrReportsTable = ""
var interval = ""

// resize modal content to max windows height
function do_resize() {
    if ($(window).width() < 768) {
        $('#detail_content').height($(window).height() - 280);
        $('#clientTab').tabdrop();
    } else {
        $('#detail_content').height($(window).height() - 230);
    }
}
$(window).resize(do_resize);

// using jQuery
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
var csrftoken = getCookie('csrftoken');

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
    timeout:500,
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

// grid/list view
$(document).on('click','.grid_list', function (e) {
    $(".grid_list").removeClass('active')
	    if($(this).hasClass('list')) {
	        $('#deviceList').removeClass('grid').addClass('list');
          $(this).addClass('active');
	    }
	    else if ($(this).hasClass('grid')) {
	        $('#deviceList').removeClass('list').addClass('grid');
          $(this).addClass('active');
	    }
});

// filter devices
$(document).on('click','.filterDevices', function (e) {
    if ($(this).hasClass('active')) {
        history.pushState('', '', '/reports/');
        getClientTable("");
        $(this).removeClass('active');
    } else {
        $(".filterDevices").removeClass('active')
        if($(this).hasClass('vm')) {
            history.pushState('', '', '?hardware=vm');
            getClientTable("hardware=vm");
            $(this).addClass('active');
        }
        else if ($(this).hasClass('mac')) {
            history.pushState('', '', '?hardware=mac');
            getClientTable("hardware=mac");
            $(this).addClass('active');
        }
        else if ($(this).hasClass('macbook')) {
            history.pushState('', '', '?hardware=macbook');
            getClientTable("hardware=macbook");
            $(this).addClass('active');
        }
        else if ($(this).hasClass('warnings')) {
            history.pushState('', '', '?show=warnings');
            getClientTable("show=warnings");
            $(this).addClass('active');
        }
        else if ($(this).hasClass('errors')) {
            history.pushState('', '', '?show=errors');
            getClientTable("show=errors");
            $(this).addClass('active');
        }
        else if ($(this).hasClass('activity')) {
            history.pushState('', '', '?show=activity');
            getClientTable("show=activity");
            $(this).addClass('active');
        }
    }
});

// search field
$(document).on('keyup','#listSearchField', function () {
	filter = $(this).val();
	$("#deviceList li").each(function() {
    if ($(this).text().search(new RegExp(filter, "i")) > -1) {
      $(this).show();
    } else {
      $(this).hide();
    }
  });
});

$(document).on('click','.manifestItem', function (e) {
    e.preventDefault()
    if($(this).hasClass('active')) {
        removeDeleteButton(this);
        $(this).removeClass('active');
    } else {
        item = $("#SoftwareView").find('.manifestItem')
        $(item).removeClass('active');
        removeDeleteButton(item);
        if(! $(this).is('input')) {
            addDeleteButton(this);
            $(this).addClass('active');
        }
    }
});

$(document).on('click','.form-control', function (e) {
    $('.manifestItem').removeClass('active');
    removeDeleteButton('.manifestItem');
});

$(document).on('click','.workflows', function (e) {
    if($(this).hasClass('active')) {
        workflowName = " "
        $(this).removeClass('active');
    } else {
        workflowName = $(this).find(':first-child').text();
        item = $("#imagrworkflow").find('.workflows');
        $(item).removeClass('active');
        $(this).addClass('active');
    } 
    setWorkflow(workflowName);
});

// reset url on modal close
$(document).on('hide.bs.modal','#computerDetails', function () {
  // check for unsaved changes
  if ($('#save_and_cancel').length && !$('#save_and_cancel').hasClass('hidden')) {
      $('#computerDetails').data('bs.modal').isShown = false;
      $("#saveOrCancelConfirmationModal").modal("show");
      event.preventDefault();
      return;
  } else {
    $('#computerDetails').data('bs.modal').isShown = true;
    stopRefresh();
    window.location.hash = '';
    current_pathname = "";
  }
});

$(document).ready(function() {
    hash = window.location.hash;
    if (hash.length > 1) {
        getComputerItem(hash.slice(1));
    }

    //$('#listSearchField').focus();
    // When a modal is shown, and it contains an <input>, make sure it's
    // selected when the modal is shown.
    $(document).on('shown.bs.modal', '.modal', function(event){
        $(event.currentTarget).find('input').select();
    });

    $(window).on('hashchange', function() {
        hash = window.location.hash;
        if (hash.length > 1) {
            if (hash.slice(1) != current_pathname) {
                getComputerItem(hash.slice(1));
                
            }
        }
    });
});

function getDeviceIcon(serial, iconid) {
    var image_url = "https://km.support.apple.com.edgekey.net/kb/securedImage.jsp?configcode="+serial.slice( 8 )+"&size=120x120"
    var $image = $("#"+serial+iconid);
    var $downloadingImage = $("<img>");
    $downloadingImage.load(function(){
        $image.attr("src", $(this).attr("src"));	
    });
    $downloadingImage.attr("src", image_url);   
}

var current_pathname = "";
function getComputerItem(pathname) {
    $('.progress-bar').css('width', '0%').attr('aria-valuenow', "0");
    showProgressBar();
    var manifestItemURL = '/reports/' + pathname;
    $.ajax({
        xhr: function() {
                var xhr = new window.XMLHttpRequest();
                xhr.addEventListener("progress", function(e) {
                    var pro = (e.loaded / e.total) * 100;
                    $('.progress-bar').css('width', pro + '%').attr('aria-valuenow', pro);
                }, false);
                return xhr;
            },
        method: 'GET',
        url: manifestItemURL,
        timeout: 10000,
        cache: false,
        success: function(data) {
            // load date
            $('#computer_detail').html(data);

            //loading manifest data
            getManifest(pathname, function(data) {
                getSoftwareList(data.catalogs, function() {
                    getListElement(pathname, "included_manifests");
                    getListElement(pathname, "catalogs");
                    getSoftwareElemnts(pathname, "managed_installs");
                    getSoftwareElemnts(pathname, "managed_uninstalls");
                    getSoftwareElemnts(pathname, "optional_installs");
                });
            })  

            current_pathname = pathname;
            requested_pathname = "";

            window.history.replaceState({'computer_detail': data}, manifestItemURL, '/reports/');
            window.location.hash = pathname;

            if (!$('#computerDetails').hasClass('in')){
                do_resize();              
                $("#computerDetails").modal("show");
                $( "#catalogs" ).sortable({
                    update: function( ) {
                     saveManifest(pathname, "catalogs");
                    }
                });
                $( "#included_manifests" ).sortable({
                    update: function( ) {
                     saveManifest(pathname, "included_manifests");
                    }
                });
            }
            hideProgressBar();

            //start refresh
            startRefresh();
        },
        error: function(jqXHR, textStatus, errorThrown) {
            $('#computer_detail').html("")
            current_pathname = "";
            $("#errorModalTitleText").text("computer read error");
             try {
                 var json_data = $.parseJSON(jqXHR.responseText)
                 if (json_data['result'] == 'failed') {
                     $("#errorModalDetailText").text(json_data['detail']);
                     $("#errorModal").modal("show");
                     return;
                 }
             } catch(err) {
                 // do nothing
             }
             $("#errorModalDetailText").text(errorThrown);
             $("#errorModal").modal("show");
			hideProgressBar();
        },
        dataType: 'html'
    })
}

//create software list
var catalogData = ""
function getSoftwareList(catalogList, handleData) {
    catalogData = ""
    $.ajax({
        type:"POST",
        url:"/reports/_catalogJson",
        data: {catalogList},
        dataType: 'json',
        success: function(data){
            catalogData = data;
            handleData(catalogData)
        }
    });
}

// includet manifests and catalogs
function getListElement(manifest, listid) {
    getManifest(manifest, function(data) {
        createListElements(data[listid], listid)
    })
}

// managed installs
function getSoftwareElemnts(manifest, listid) {
    getManifest(manifest, function(data) {
        $( "#"+listid).empty()
        loopSoftwareElements(data[listid], listid);

        $( "#"+listid+"_remote").empty()
        getSoftwareElemntsIncludedManifest(data.included_manifests, listid);
    })
}

function getSoftwareElemntsIncludedManifest(manifests, listid) {
    $.each(manifests, function( index, manifest ) {
        getManifest(manifest, function(data) {
            loopSoftwareElements(data[listid], listid+"_remote", manifest);
            getSoftwareElemntsIncludedManifest(data.included_manifests, listid);
        })
    });
}

// edit list
function createListElements(elements, listid) {
    $( "#"+listid ).empty()
    $.each(elements, function( index, value ) {
        $( "#"+listid ).append( "<a class='list-group-item manifestItem' id='"+listid+"_"+value+"'>"+value+"</a>" );
    });
    $( "#"+listid ).append( "<input type='text' id='"+listid+"' autocomplete=\"off\" class='list-group-item form-control "+listid+"' style='padding-bottom:19px; padding-top:20px;' onkeypress='addElementToList(this, \""+listid+"\", event)'>" );

    if(listid == "catalogs") {
        getTypeahead("/api/catalogs?api_fields=filename", listid);
    } else {
        getTypeahead("/api/manifests?api_fields=filename", listid);
    }
    $( "."+listid+"" ).focus()
}

function getManifest(manifest, handleData) {
    $.ajax({
        method: 'GET',
        url: "/reports/_getManifest/"+manifest,
        timeout: 10000,
        cache: false,
        success: function(data) {
            handleData(JSON.parse(data));
        },
        error: function(jqXHR, textStatus, errorThrown) {
            //display error when manifest is not readable
            //$("#SoftwareView").append('<div class="row" id="manifestWarning"><div class="col-md-12"><div class="alert alert-warning">No manifest found! <a class="alert-link" onclick="newManifestItem();">create</a></div></div></div>');
        },
        dataType: 'html'
    });
}

function addElementToList(item, listid, event) {
    if (event.which == '13' && item.value != "") {
        manifest = getManifestName()
        itemValue = item.value

        //get items to save
        itemList = getItemsToSave(listid)

        //check if item already in list
        if(jQuery.inArray(itemValue, itemList) == -1) {
            itemList.push(itemValue);

            itemList = JSON.stringify(itemList);

            $.ajax({
                type:"POST",
                url:"/api/manifests/"+manifest,
                method: "PATCH",
                data: '{ "'+[listid]+'": '+itemList+' }',
                contentType: 'application/json',
                success: function(data){
                    if (listid === 'included_manifests') {
                        getListElement(manifest, listid);
                        getSoftwareElemntsIncludedManifest([itemValue], "managed_installs")
                        getSoftwareElemntsIncludedManifest([itemValue], "managed_uninstalls")
                        getSoftwareElemntsIncludedManifest([itemValue], "optional_installs")
                    } else if (listid === 'catalogs') {
                        getManifest(manifest, function(data) {
                            getSoftwareList(data.catalogs, function() {
                                getListElement(manifest, "included_manifests");
                                getListElement(manifest, "catalogs");
                                getSoftwareElemnts(manifest, "managed_installs");
                                getSoftwareElemnts(manifest, "managed_uninstalls");
                                getSoftwareElemnts(manifest, "optional_installs");
                            });
                        });
                    } else {
                        $( "#"+listid).empty()
                        loopSoftwareElements(data[listid], listid);
                    }
                },
                error: function(){
                    alert("could not save "+itemValue+"!");
                }
            });
        }
    }
}

function removeElementFromList(item, listid) {
    manifest = getManifestName();
    elementToRemove = $(item).parent().attr('id')
    itemValue = $(item).parent().attr('id').split(/[_ ]+/).pop()
    if($.isNumeric(parseInt(itemValue))) {
        length = $(item).parent().attr('id').length - $(item).parent().attr('id').split(/[_ ]+/).pop().length - 1
        itemValue = $(item).parent().attr('id').substring(0, length);
    }

    //get items to save
    itemList = getItemsToSave(listid);
    itemList.splice(itemList.indexOf(itemValue), 1);
    itemList = JSON.stringify(itemList);

    $.ajax({
        type:"POST",
        url:"/api/manifests/"+manifest,
        method: "PATCH",
        data: '{ "'+[listid]+'": '+itemList+' }',
        contentType: 'application/json',
        success: function(data){
            if (listid === 'included_manifests'){
                getListElement(manifest, listid);
                $( "#managed_installs_remote").empty()
                getSoftwareElemntsIncludedManifest(data.included_manifests, "managed_installs")
                $( "#managed_uninstalls_remote").empty()
                getSoftwareElemntsIncludedManifest(data.included_manifests, "managed_uninstalls")
                $( "#optional_installs_remote").empty()
                getSoftwareElemntsIncludedManifest(data.included_manifests, "optional_installs")
            }  else {
                getManifest(manifest, function(data) {
                    getSoftwareList(data.catalogs, function() {
                        getListElement(manifest, "included_manifests");
                        getListElement(manifest, "catalogs");
                        getSoftwareElemnts(manifest, "managed_installs");
                        getSoftwareElemnts(manifest, "managed_uninstalls");
                        getSoftwareElemnts(manifest, "optional_installs");
                    });
                })
            }
        },
        error: function(){
            alert("could not remove "+item+"!");
        }
    });
}

function saveManifest(manifest, listid) {
    //get items to save
    itemList = getItemsToSave(listid);
    itemList = JSON.stringify(itemList);

    $.ajax({
        type:"POST",
        url:"/api/manifests/"+manifest,
        method: "PATCH",
        data: '{ "'+[listid]+'": '+itemList+' }',
        contentType: 'application/json',
        error: function(){
            alert("could not save manifest "+manifest+"!");
        }
    });
}


// edit software
function loopSoftwareElements(elements, listid, require_update) {
    var match = listid.match("remote");
    if(!match) {
        $( "#"+listid ).append("<input type='text' class='list-group-item form-control software' style='padding-bottom:19px; padding-top:20px;' onkeypress='addSoftwareToList(this, \""+listid+"\", event)'>" );
        $(".software").typeahead({
            source: Object.keys(catalogData),
            autoSelect: true
        });
        $( "#"+listid+" .software" ).focus()
    }
    $.each(elements, function( index, value ) {
        createSoftwareElement(value, listid, require_update);
    });
}

var softwareElementCount = 0
function createSoftwareElement(element, addTo, require_update) {
        var itemID = element + "_" + softwareElementCount
        var listGroupID = element + "_" + softwareElementCount + "_" + addTo
        var additionalClass = " "

        //item infos
        var display_name = element
        var version = ""
        var icon = ""

        if (typeof require_update === 'undefined') {
            require_update = ""
            additionalClass += "manifestItem"
        }
        if (typeof catalogData[element] === 'undefined') {
            additionalClass += " list-group-item-danger"
        } else {
            display_name = catalogData[element].display_name
            version = catalogData[element].version
            var icon = catalogData[element].icon
        }

        $( "#"+addTo ).append( "<a href='#' class='list-group-item "+additionalClass+"' id="+itemID+"><img src='"+static_url+"img/GenericPkg.png' width='15' style='margin-top:-3px;' id="+itemID+'_icon'+">  "+display_name+" "+version+" <small class='pull-right'> "+require_update+"<div class='led-box status pull-right'><div class='led-grey'></div></div></small></a>" );
        $( "#"+itemID ).after('<div class="list-group" style="padding-left:20px;" id="'+listGroupID+'"></div>');
        
        var serial = getSerial();
        getStatus(element, serial, itemID);

        //icon
        if (icon !== '') {
            $.get(icon).done(function() { 
                document.getElementById(itemID+'_icon').src = icon;
            }).fail(function() { 
                document.getElementById(itemID+'_icon').src = static_url + "/img/GenericPkg.png"
            })
        }

        if (typeof catalogData[element] !== 'undefined' && typeof catalogData[element].requires !== 'undefined') {
            $.each(catalogData[element].requires, function( index, element_requires ) {
                createSoftwareElement(element_requires, listGroupID, catalogData[element].display_name+" requires");
            });
        }

       if (typeof catalogData[element] !== 'undefined' && typeof catalogData[element].updates !== 'undefined') {
           $.each(catalogData[element].updates, function( index, element_updates ) {
               createSoftwareElement(element_updates, listGroupID, "update for "+catalogData[element].display_name);
           });
        }
      softwareElementCount++;
}

function addSoftwareToList(item, listid, event) {
    if (event.which == '13' && item.value != "") {
        manifest = getManifestName()
        itemValue = item.value

        //get items to save
        itemList = getItemsToSave(listid)

        //check if item already in list
        if(jQuery.inArray(itemValue, itemList) == -1) {
            itemList.unshift(itemValue);

            itemList = JSON.stringify(itemList);
            $.ajax({
                type:"POST",
                url:"/api/manifests/"+manifest,
                method: "PATCH",
                data: '{ "'+[listid]+'": '+itemList+' }',
                contentType: 'application/json',
                success: function(data){
                    $( "#"+listid).empty()
                    loopSoftwareElements(data[listid], listid);
                },
                error: function(){
                    alert("could not save "+itemValue+"!");
                }
            });
        }
    }
}

function getStatus(item, serial, id) {
    $.ajax({
        type:"POST",
        url:"/reports/_status",
        data: {item : item, serial: serial},
        dataType: 'json',
        success: function(data){
            $('#'+id).find('.led-box').children().removeClass().addClass( data );
        }
    }); 
}

function loadStatus() {
    $('.status').each(function(i, obj) {
        //get id
        var id = $(obj).parent().parent().attr('id');
        if (typeof id  !== "undefined") {
            // item
            var item = id.split('_')
            item.pop()
            item = item.join("_");
        
            //get serial
            var serial = getSerial();

            getStatus(item, serial, id)
        }
    });
}

function getSerial() {
    var serial = window.location.hash
    serial.slice(1)
    return serial.substring(1)
}

function getManifestName() {
    return $("#manifestName").attr('value')
}

//edit software
function getItemsToSave(listid) {
    //get items to save
    itemList = $('#'+listid).children('.manifestItem').map(function() {
        if(this.id.match("^"+listid)) { 
            return this.id.substring(listid.length + 1); 
        } 
        else {
            idLength = this.id.length - (this.id.split(/[_ ]+/).pop().length + 1)
            return this.id.substring(0, idLength);
        }
    }).get()
    return itemList
}

function getClientTable(filter) {
    showProgressBar();
    var manifestItemURL = '/reports/?'+filter;
    $.ajax({
        xhr: function() {
                var xhr = new window.XMLHttpRequest();
                xhr.addEventListener("progress", function(e) {
                    var pro = (e.loaded / e.total) * 100;
                    $('.progress-bar').css('width', pro + '%').attr('aria-valuenow', pro);
                }, false);
                return xhr;
            },
        method: 'GET',
        url: manifestItemURL,
        timeout: 10000,
        cache: false,
        success: function(data) {
            $('#clienttable').html(data);
            hideProgressBar();
        },
        error: function(jqXHR, textStatus, errorThrown) {
            $('#clienttable').html("");
            $("#errorModalTitleText").text("computer list read error");
             try {
                 var json_data = $.parseJSON(jqXHR.responseText)
                 if (json_data['result'] == 'failed') {
                     $("#errorModalDetailText").text(json_data['detail']);
                     $("#errorModal").modal("show");
                     return;
                 }
             } catch(err) {
                 // do nothing
             }
             $("#errorModalDetailText").text(errorThrown);
             $("#errorModal").modal("show");
                hideProgressBar();
        },
        dataType: 'html'
    })
}

function addDeleteButton(id) {
    $(id).append("<i class='row_del_btn fa fa-minus-circle pull-right delete' onclick='removeElementFromList(this, \""+$(id).parent().attr('id')+"\")'></i>");
}

function removeDeleteButton(id) {
    $(id).find(".delete").remove();
}

function showProgressBar() {
    $('.progress-bar').css('width', '0%').attr('aria-valuenow', "0");
    $("#site-loading-bar").fadeIn(1);
}

function hideProgressBar() {
     $("#site-loading-bar").fadeOut(1000);
}

function getImagrReports(serial) {
        imagrReportsTable = $('#imagrreports').DataTable( {
        "sAjaxSource": "/api/imagr/"+serial,
        "sAjaxDataProp": "",
        "aoColumns": [
            { "mDataProp": "date_added", "sWidth": "155px", "mRender": function (data) {
                var date = new Date(data);
                var month = date.getMonth() + 1;
                return date.getDate() + "." + (month.length > 1 ? month : "0" + month) + "." + date.getFullYear() + " - " + (date.getHours() < 10 ? '0' : '') + date.getHours()+":"+(date.getMinutes() < 10 ? '0' : '') + date.getMinutes()+":"+(date.getSeconds() < 10 ? '0' : '') + date.getSeconds();
            }},
            { "mDataProp": "message" },
            { "mDataProp": "status", "sWidth": "80px", },
        ],
        "fnRowCallback": function( nRow, aData, iDisplayIndex, iDisplayIndexFull ) {
			if ( aData['status'] == "in_progress" ) {
				$('td', nRow).addClass('info');
			} else if ( aData['status'] == "success" ) {
				$('td', nRow).addClass('success');
			} else if ( aData['status'] == "error" ) {
				$('td', nRow).addClass('danger');
			} 
		},
        "bAutoWidth": false,
        "sDom": "<t>",
         "bPaginate": false,
         "bInfo": false,
         "bFilter": true,
         "bStateSave": false,
         "aaSorting": [[0,'desc']]
    } );
}

function newManifestItem() {
    var pathname = getManifestName();
    var manifestItemURL = '/api/manifests/' + pathname;
    $.ajax({
        method: 'POST',
        url: manifestItemURL,
        timeout: 10000,
        cache: false,
        success: function(data) {
            getManifest(pathname);
        },
        error: function(jqXHR, textStatus, errorThrown) {
            $("#errorModalTitleText").text("Manifest creation error");
            try {
                var json_data = $.parseJSON(jqXHR.responseText)
                if (json_data['result'] == 'failed') {
                    $("#errorModalDetailText").text(json_data['detail']);
                    $("#errorModal").modal("show");
                    return;
                }
            } catch(err) {
                // do nothing
            }
        },
    });
}

function deleteMachine() {
    var machineURL = '/api/report/' + current_pathname;
    $.ajax({
        method: 'POST',
        url: machineURL,
        headers: {'X-METHODOVERRIDE': 'DELETE'},
        success: function(data) {
            getClientTable();
            $('#computerDetails').modal('hide');
        },
        error: function(jqXHR, textStatus, errorThrown) {
            $("#errorModalTitleText").text("Machine delete error");
            try {
                var json_data = $.parseJSON(jqXHR.responseText)
                if (json_data['result'] == 'failed') {
                    $("#errorModalDetailText").text(json_data['detail']);
                    $("#errorModal").modal("show");
                    return;
                }
            } catch(err) {
                // do nothing
            }
            $("#errorModalDetailText").text(errorThrown);
            $("#errorModal").modal("show");
        }
    });;
}

function deleteManifest() {
     var manifestItemURL = '/api/manifests/' + current_pathname;
    $.ajax({
        method: 'POST',
        url: manifestItemURL,
        headers: {'X-METHODOVERRIDE': 'DELETE'},
        success: function(data) {
            //
        },
        error: function(jqXHR, textStatus, errorThrown) {
            if(jqXHR.status==404) {
            // ignore 404
            } else {
                $("#errorModalTitleText").text("Manifest delete error");
                try {
                    var json_data = $.parseJSON(jqXHR.responseText)
                    if (json_data['result'] == 'failed') {
                        $("#errorModalDetailText").text(json_data['detail']);
                        $("#errorModal").modal("show");
                        return;
                    }
                } catch(err) {
                    // do nothing
                }
                $("#errorModalDetailText").text(errorThrown);
                $("#errorModal").modal("show");
            }
        }
    });;
}

function deleteMachineAndManifest() {
    deleteManifest();
    deleteMachine();
}

function setWorkflow(workflow) {
    event.preventDefault();
    var machineURL = '/api/report/' + current_pathname;
    $.ajax({
        method: 'POST',
        url: machineURL,
        data: { imagr_workflow : workflow },
        success: function(data) {
            //set active
        },
        error: function(jqXHR, textStatus, errorThrown) {
            $("#errorModalTitleText").text("workflow set error");
            try {
                var json_data = $.parseJSON(jqXHR.responseText)
                if (json_data['result'] == 'failed') {
                    $("#errorModalDetailText").text(json_data['detail']);
                    $("#errorModal").modal("show");
                    return;
                }
            } catch(err) {
                // do nothing
            }
            $("#errorModalDetailText").text(errorThrown);
            $("#errorModal").modal("show");
        }
    });
}

function getTypeahead(url, listid) {
    $.ajax({
        method: 'GET',
        url: url,
        success: function(data) {
            var sourceArr = [];
            for (var i = 0; i < data.length; i++) {
                sourceArr.push(data[i].filename);
            }
            $("."+listid).typeahead({
                source: sourceArr,
                autoSelect: true
            });
        },
        error: function(jqXHR, textStatus, errorThrown) {
        }
    });
    
}

function startRefresh() {
    // 2 second interval
    interval = setInterval (function () {
        //imagr workflow
        imagrReportsTable.ajax.reload();
        loadStatus();
    }, 2000);
}

function stopRefresh() {
    try{
        clearInterval(interval);
    }catch(err){}
}