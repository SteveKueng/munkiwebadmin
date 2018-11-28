//global var
var passwordAccessTable = ""
var interval = ""
var selectedGroupID = ""

window.confirm = function(message, cb) {
    $("#confirmationModal .modal-body").html(message);
    $("#confirmationModal").modal('show');
    $("#confirmYes").unbind('click').on("click", function () {
        cb(true);
    });
    cb(false);
};

// resize modal content to max windows height
function do_resize() {
    if ($(window).width() < 768) {
        $('#detail_content').height($(window).height() - 280);
    } else {
        $('#detail_content').height($(window).height() - 230);
    }
}
$(window).resize(do_resize);

// using jQuery
// function getCookie(name) {
//     var cookieValue = null;
//     if (document.cookie && document.cookie !== '') {
//         var cookies = document.cookie.split(';');
//         for (var i = 0; i < cookies.length; i++) {
//             var cookie = jQuery.trim(cookies[i]);
//             // Does this cookie string begin with the name we want?
//             if (cookie.substring(0, name.length + 1) === (name + '=')) {
//                 cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
//                 break;
//             }
//         }
//     }
//     return cookieValue;
// }
// var csrftoken = getCookie('csrftoken');

// function csrfSafeMethod(method) {
//     // these HTTP methods do not require CSRF protection
//     return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
// }
// $.ajaxSetup({
//     timeout:10000,
//     beforeSend: function(xhr, settings) {
//         if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
//             xhr.setRequestHeader("X-CSRFToken", csrftoken);
//         }
//     }
// });

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

$(document).on('click','.tab', function (e) {
    hash = window.location.hash;
    window.location.hash = hash.slice(1).split('#')[0] + $(event.target).context.hash
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

$(document).on('click','#showPassButton', function (e) {
    e.preventDefault()
    reason = $('#showPass').find('textarea').val()
    if (reason.length) {
        showPassword(reason)
    } else {
        $("#errorModalDetailText").text("No reason submited");
        $("#errorModal").modal("show");
    }
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
    $('.modal-backdrop').hide();
    window.location.hash = '';
    current_pathname = "";
    window.stop()
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
            if (hash.slice(1).split('#')[0] != current_pathname) {
                $('.modal-backdrop').hide();
                getComputerItem(hash.slice(1));
            }
        }
    });
});

function activaTab(tab){
  $('.nav-tabs a[href="#' + tab + '"]').tab('show');
};

function getDeviceIcon(serial, iconid) {
    var image_url = "https://support.apple.com/kb/securedImage.jsp?configcode="+serial.slice( 8 )+"&size=120x120"
    var $image = $("#"+serial+iconid);
    var $downloadingImage = $("<img>");
    $downloadingImage.load(function(){
        $image.attr("src", $(this).attr("src"));	
    });
    $downloadingImage.attr("src", image_url);   
}

var current_pathname = "";
function getComputerItem(pathname) {
    var serial = pathname.split('#')[0];
    var tab = pathname.split('#')[1];

    $('.progress-bar').css('width', '0%').attr('aria-valuenow', "0");
    showProgressBar();
    getInitialManifest(serial, function(manifest) {
        var reportItemURL = '/reports/' + serial;
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
            url: reportItemURL,
            cache: false,
            success: function(data) {
                // load date
                $('#computer_detail').html(data);
    
                //loading manifest data
                getManifest(manifest, function(data) {
                    getSoftwareList(data.catalogs, function() {
                        getListElement(manifest, "included_manifests");
                        getListElement(manifest, "catalogs");
                        getSoftwareElemnts(manifest, "managed_installs");
                        getSoftwareElemnts(manifest, "managed_uninstalls");
                        getSoftwareElemnts(manifest, "optional_installs");
                    });
                })  
    
                current_pathname = serial;
                requested_pathname = "";
    
                window.history.replaceState({'computer_detail': data}, reportItemURL, '/reports/');
                window.location.hash = pathname;
    
                if (!$('#computerDetails').hasClass('in')){
                    do_resize();              
                    $("#computerDetails").modal("show");
                    $( "#catalogs" ).sortable({
                        update: function( ) {
                        saveManifest(manifest, "catalogs");
                        }
                    });
                    $( "#included_manifests" ).sortable({
                        update: function( ) {
                        saveManifest(manifest, "included_manifests");
                        }
                    });
                }
    
                getDeviceIcon(serial, "_iconDetail");
                //getImagrReports(serial);
                loadPasswordAccess(serial);
                getMDMDeviceInfo(serial);
                get_model_description(serial);
                if (tab) {
                    activaTab(tab);
                }
                hideProgressBar();
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
    });
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
        cache: false,
        success: function(data) {
            handleData(JSON.parse(data));
        },
        error: function(jqXHR, textStatus, errorThrown) {
            //display error when manifest is not readable
            $("#errorModalTitleText").text("manifest list read error");
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
                error: function(jqXHR, textStatus, errorThrown) {
                    //display error when manifest is not readable
                    $("#errorModalTitleText").text("save error");
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
                },
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
            if (listid === 'included_manifests') {
                getListElement(manifest, listid);
                $( "#managed_installs_remote").empty()
                getSoftwareElemntsIncludedManifest(data.included_manifests, "managed_installs")
                $( "#managed_uninstalls_remote").empty()
                getSoftwareElemntsIncludedManifest(data.included_manifests, "managed_uninstalls")
                $( "#optional_installs_remote").empty()
                getSoftwareElemntsIncludedManifest(data.included_manifests, "optional_installs")
            } else if (listid === 'catalogs') {
                getManifest(manifest, function(data) {
                    getSoftwareList(data.catalogs, function() {
                        getListElement(manifest, "included_manifests");
                        getListElement(manifest, "catalogs");
                        getSoftwareElemnts(manifest, "managed_installs");
                        getSoftwareElemnts(manifest, "managed_uninstalls");
                        getSoftwareElemnts(manifest, "optional_installs");
                    });
                })
            } else {
                $( "#"+listid).empty()
                loopSoftwareElements(data[listid], listid);
            }
        },
        error: function(jqXHR, textStatus, errorThrown) {
            //display error when manifest is not readable
            $("#errorModalTitleText").text("remove error");
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
        },
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
        error: function(jqXHR, textStatus, errorThrown) {
            //display error when manifest is not readable
            $("#errorModalTitleText").text("manifest save error");
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
        },
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

    $.ajax({
        type:"POST",
        url:"/reports/_status",
        data: {item : element, serial: current_pathname},
        dataType: 'json',
        success: function(data){
            status = data
        },
        error: function(){
            status = "led-grey"
        },
    }).done(function(){
        $( "#"+addTo ).append( "<a href='#' class='list-group-item "+additionalClass+"' id="+itemID+"><img src='"+static_url+"img/GenericPkg.png' width='15' style='margin-top:-3px;' id="+itemID+'_icon'+">  "+display_name+" "+version+" <small class='pull-right'> "+require_update+"<div class='led-box status pull-right'><div class='" + status + "'></div></div></small></a>" );
        $( "#"+itemID ).after('<div class="list-group" style="padding-left:20px;" id="'+listGroupID+'"></div>');

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
    }); 

    
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
                error: function(jqXHR, textStatus, errorThrown) {
                    //display error when manifest is not readable
                    $("#errorModalTitleText").text("save error");
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
                },
            });
        }
    }
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
    var reportItemURL = '/reports/?'+filter;
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
        url: reportItemURL,
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

function newManifestItem() {
    var pathname = getManifestName();
    var manifestItemURL = '/api/manifests/' + pathname;
    $.ajax({
        method: 'POST',
        url: manifestItemURL,
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
    var machineURL = '/api/report/'+current_pathname;
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
    var machineURL = '/api/report/'+current_pathname;
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

function getInitialManifest(serial, handleData) {
    var defautlManifestTyp = $("#defaultManifestType").attr('value');
    if (defautlManifestTyp == "hostname") {
        getHostname(serial, function(hostname){
            handleData(hostname)
        })
    } else {
        handleData(serial)
    }
}

function getHostname(serial, handleData) {
    $.ajax({
        method: 'GET',
        url: "/api/report/"+serial+"?api_fields=hostname",
        cache: false,
        success: function(data) {
            handleData(JSON.parse(data)[0]["fields"]["hostname"])
        },
        error: function(jqXHR, textStatus, errorThrown) {
            //display error when manifest is not readable
            $("#errorModalTitleText").text("could not get hostname");
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
        },
        dataType: 'html'
    });
}

function loadPasswordAccess(serial) {
    var machineURL = '/api/vault/reasons/'+serial;
    passwordAccessTable = $('#passwordAccess').DataTable( {
    ajax: {
        url: machineURL,
        dataSrc: ''
    },
    columns: [
        { data: 'fields.user.0' },
        { data: 'fields.reason' },
        { data: 'fields.date', type: 'date' },
    ],
    "columnDefs": [
        {
            "render": function ( data, type, row ) {
                return new Date(data)
            },
            "width": "100px",
            "targets": 2
        },
    ],
    "bPaginate": false,
    "bInfo": false,
    "bFilter": false,
    "aaSorting": [[2,"desc"]]
    } );
}

function showPassword(reason) {
    var machineURL = '/api/vault/show/'+current_pathname;
    $.ajax({
        method: 'POST',
        url: machineURL,
        data: { "reason" : reason},
        success: function(data) {
            var html = data + ' <button type="button" class="btn btn-default btn-xs" onclick="copyTextToClipboard(\'' + data + '\');"><i class="fa fa-clipboard" aria-hidden="true"></i></button>'
            $("#password").html( html );
            $("#reasonForm").addClass("hidden")
            $("#showPassTable").removeClass("hidden")
            passwordAccessTable.ajax.reload();
        },
        error: function(jqXHR, textStatus, errorThrown) {
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


function get_model_description(serial) {
    $.ajax({
        url: '/reports/model/' + serial,
        type: 'GET',
        dataType: 'html',
        success: function(data, textStatus, xhr) {
            $('#machineModel').html(data)
        },
        error: function(xhr, textStatus, errorThrown) {
            //alert(errorThrown)
        },
    });
}

function getMDMDeviceInfo(serail) {
    var machineURL = '/api/mdm/devices/'+serail;
    $.ajax({
        method: 'GET',
        url: machineURL,
        success: function(data) {
            var html = '<div class="col-lg-6">';
            html += '<ul class="list-group">';
            if (data) {
                var attributes = data['data']['attributes']
                var element = 0;
                $.each(attributes, function(key, value) {
                    if(element == 12){
                        html += '<div class="col-lg-6">';
                        html += '<ul class="list-group">';
                    }
                    if(value) {
                        codeStyle = ""
                        if(key == "firmware_password" || key == "filevault_recovery_key") {
                            codeStyle = 'font-family: Consolas, Menlo, Monaco, Lucida Console, Liberation Mono, DejaVu Sans Mono, Bitstream Vera Sans Mono, Courier New, monospace, serif;';
                        }
                        html += '<li class="list-group-item" style="text-transform: capitalize;"><b>'+key.replace(/_/g, " ")+':</b><span class="pull-right" style="text-transform: none; '+codeStyle+'">'+value+'</span></li>';
                        element = element + 1;
                    }
                    if(element == 12) {
                        html += '</ul>'
                        html += '</div>'
                    }
                });
                
                //get device groups
                getMDMDeviceGroupInfo(data['data']['id'], data['data']['relationships']['device_group']['data']['id']);

                //get app groups
                getAppGroups(data['data']['id']);    
            } else {
                html += '<li class="list-group-item">no data</li>'
            }
            html += '</ul>'
            html += '</div>'
            
            //add html
            $('#mdmDetail').html(html);
        },
        error: function(jqXHR, textStatus, errorThrown) {
            var html = '';
            html += '<div class="col-lg-6">'
            html += '<ul class="list-group">'
            html += '<li class="list-group-item">no data</li>'
            html += '</ul>'
            html += '</div>'
            $('#mdmDetail').html(html);
        }
    });
}

function getMDMDeviceGroupInfo(clientID, currentGroupID) {
    var machineURL = '/api/mdm/device_groups';
    $.ajax({
        method: 'GET',
        url: machineURL,
        success: function(data) {
            if (data) {
                var html = '';
                var list = '';
                var buttonName = '';
                $.each(data['data'], function(key, value) {
                    list += '<li' 
                    if (currentGroupID == value['id']) {
                        buttonName = value['attributes']['name']
                        list += ' class="disabled"'
                    } 
                    list += '><a onclick="changeGroup( \''+clientID+'\', \''+value['id']+'\' )">'+value['attributes']['name']+'</a></li>';
                });

                html += '<div class="dropdown pull-right"> \
                    <button class="btn btn-primary dropdown-toggle" type="button" id="groupDrop" data-toggle="dropdown" aria-haspopup="true" aria-expanded="true">'+buttonName+'<span class="caret"></span></button> \
                    <ul class="dropdown-menu" aria-labelledby="groupDrop">'+list+'</ul></div>'
                $('#mdmSubmit').html(html);
            }
            
        },
        error: function(jqXHR, textStatus, errorThrown) {
        }
    });
}

function getAppGroups(deviceID) {
    var machineURL = '/api/mdm/app_groups';
    $.ajax({
        method: 'GET',
        url: machineURL,
        success: function(data) {
            if (data) {
                var source = [];
                var map = {};
                var html = '<div class="col-lg-12">';
                html += '<ul class="list-group">';
                $.each(data['data'], function(key, value) {
                    source.push(value['attributes']['name']);
                    map[value['attributes']['name']] = value['id'];
                    
                    value['relationships']['devices']['data'].some(function(el) {
                        if (el['id'] == deviceID){
                            html += '<li class="list-group-item" style="text-transform: capitalize;"><b>'+value['attributes']['name']+'</b><span class="pull-right"><button class="btn btn-danger btn-xs" onclick="removeDeviceFromAppGroup('+value['id']+', '+deviceID+')" ><i class="fas fa-trash" aria-hidden="true"></i></button></span></li>';
                        }
                    });
                });
                html += '</ul>'
                html += '</div>'
                $('#vppDetail').html(html);

                //typeahead
                $(".vpp_app_groups").typeahead({
                    source: source,
                    autoSelect: true,
                    updater: function (item) {
                        selectedGroupID = map[item];
                        return item;
                    }
                });
            }
        },
        error: function(jqXHR, textStatus, errorThrown) {
        }
    });
}

function changeGroup(device, group) {
    var url = '/api/mdm/device_groups/'+group + "/devices/" + device;
    confirm("<h4>Change group for device: "+current_pathname+"?</h4>", function(result) { 
        if (result) {
            $("#process_progress").modal("show");
            $.ajax({
                method: 'POST',
                url: url,
                success: function(data) {
                    getMDMDeviceInfo(current_pathname);
                    $("#process_progress").modal("hide");
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    $("#errorModalTitleText").text("MDM post error");
                    try {
                        var json_data = $.parseJSON(jqXHR.responseText)
                        if (json_data['result'] == 'failed') {
                            $("#errorModalDetailText").text(json_data['detail']);
                            $("#process_progress").modal("hide");
                            $("#errorModal").modal("show");
                            return;
                        }
                    } catch(err) {
                        // do nothing
                    }
                    $("#errorModalDetailText").text(errorThrown);
                    $("#process_progress").modal("hide");
                    $("#errorModal").modal("show");
                }
            });
        }
    }); 
}

function clientActions(action) {
    var url = '/api/mdm/devices/'+current_pathname + "/" + action ;
    confirm("<h4>"+ action +" device: "+current_pathname+"?</h4>", function(result) { 
        if (result) {
            $("#process_progress").modal("show");
            $.ajax({
                method: 'POST',
                url: url,
                success: function(data) {
                    getMDMDeviceInfo(current_pathname);
                    $("#process_progress").modal("hide");
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    $("#errorModalTitleText").text("MDM post error");
                    try {
                        var json_data = $.parseJSON(jqXHR.responseText)
                        if (json_data['result'] == 'failed') {
                            $("#errorModalDetailText").text(json_data['detail']);
                            $("#process_progress").modal("hide");
                            $("#errorModal").modal("show");
                            return;
                        }
                    } catch(err) {
                        // do nothing
                    }
                    $("#errorModalDetailText").text(errorThrown);
                    $("#process_progress").modal("hide");
                    $("#errorModal").modal("show");
                }
            });
        }
    }); 
}

function pushApps(groupID) {
    var url = '/api/mdm/app_groups/'+groupID + "/push_apps" ;
    $("#process_progress").modal("show");
    $.ajax({
        method: 'POST',
        url: url,
        success: function(data) {
            $("#process_progress").modal("hide");
        },
        error: function(jqXHR, textStatus, errorThrown) {
            $("#errorModalTitleText").text("MDM post error");
            try {
                var json_data = $.parseJSON(jqXHR.responseText)
                if (json_data['result'] == 'failed') {
                    $("#errorModalDetailText").text(json_data['detail']);
                    $("#process_progress").modal("hide");
                    $("#errorModal").modal("show");
                    return;
                }
            } catch(err) {
                // do nothing
            }
            $("#errorModalDetailText").text(errorThrown);
            $("#process_progress").modal("hide");
            $("#errorModal").modal("show");
        }
    });
}

function addDeviceToAppGroup(deviceID) {
    if (event.which == '13' && selectedGroupID != "" && deviceID != "") {
        var url = '/api/mdm/app_groups/'+selectedGroupID + "/devices/" + deviceID;
        $("#process_progress").modal("show");
        $.ajax({
            method: 'POST',
            url: url,
            success: function(data) {
                getAppGroups(deviceID);
                $("#process_progress").modal("hide");
                pushApps(selectedGroupID);
                selectedGroupID = "";
                $('.vpp_app_groups').val('')
            },
            error: function(jqXHR, textStatus, errorThrown) {
                $("#errorModalTitleText").text("MDM post error");
                try {
                    var json_data = $.parseJSON(jqXHR.responseText)
                    if (json_data['result'] == 'failed') {
                        $("#errorModalDetailText").text(json_data['detail']);
                        $("#process_progress").modal("hide");
                        $("#errorModal").modal("show");
                        return;
                    }
                } catch(err) {
                    // do nothing
                }
                $("#errorModalDetailText").text(errorThrown);
                $("#process_progress").modal("hide");
                $("#errorModal").modal("show");
            }
        });
    }
}

function removeDeviceFromAppGroup(groupID, deviceID) {
    var url = '/api/mdm/app_groups/'+groupID + "/devices/" + deviceID;
    $("#process_progress").modal("show");
    $.ajax({
        method: 'DELETE',
        url: url,
        success: function(data) {
            getAppGroups(deviceID);
            $("#process_progress").modal("hide");
        },
        error: function(jqXHR, textStatus, errorThrown) {
            $("#errorModalTitleText").text("MDM post error");
            try {
                var json_data = $.parseJSON(jqXHR.responseText)
                if (json_data['result'] == 'failed') {
                    $("#errorModalDetailText").text(json_data['detail']);
                    $("#process_progress").modal("hide");
                    $("#errorModal").modal("show");
                    return;
                }
            } catch(err) {
                // do nothing
            }
            $("#errorModalDetailText").text(errorThrown);
            $("#process_progress").modal("hide");
            $("#errorModal").modal("show");
        }
    });
}