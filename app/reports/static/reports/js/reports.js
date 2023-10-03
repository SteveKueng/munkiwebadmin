//global var
var passwordAccessTable = ""
var interval = ""

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
    window.location.href = $(event.target).context.hash
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

$(document).ready(function() {
    getClientTable();
    hash = window.location.hash;
    if (hash.length > 1) {
        getComputerItem(hash.slice(1));
    }

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

function cancelEdit() {
    history.replaceState({}, document.title, ".");
    current_pathname = "";
    $("#computerDetails").modal("hide");
}

function activaTab(tab){
  $('.nav-tabs a[href="#' + tab + '"]').tab('show');
};

var current_pathname = "";
function getComputerItem(pathname) {
    var serial = pathname.split('#')[0];
    var tab = pathname.split('#')[1];

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

                if (tab) {
                    activaTab(tab);
                }
    
                loadPasswordAccess(serial);
                loadInventory(serial);
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

function getClientTable() {
    $('#list_items').dataTable({
        ajax: {
            url: '/reports/_json',
            dataSrc: '',
            complete: function(jqXHR, textStatus){
                $('#process_progress').modal('hide');
              },
        },
        columns: [
            { data: 'img_url' },
            { data: 'hostname' },
            { data: 'serial_number' },
            { data: 'username' },
            { data: 'machine_model' },
            { data: 'cpu_type' },
            { data: 'os_version' }
        ],
        "sDom": "<t>",
        "bPaginate": false,
        //"scrollY": "100vh",
        "bInfo": false,
        "autoWidth": false,
        "bFilter": true,
        "bStateSave": false,
        "aaSorting": [[0,'asc']],
        "columnDefs": [
            { "targets": 0,
              "render": render_img,
            }
        ],
        responsive: {
            details: false
        }
    })
    // tie our search field to the table
    var thisTable = $('#list_items').DataTable(),
        searchField = $('#listSearchField');
    searchField.keyup(function(){
        thisTable.search($(this).val()).draw();
    });
     
    let table = new DataTable('#list_items');
    table.on('click', 'tbody tr', function () {
        let data = table.row(this).data();
        var url = window.location.href;
        window.location.href = url + '#' + data['serial_number'];
    });

}

function addDeleteButton(id) {
    $(id).append("<i class='row_del_btn fa fa-minus-circle pull-right delete' onclick='removeElementFromList(this, \""+$(id).parent().attr('id')+"\")'></i>");
}

function removeDeleteButton(id) {
    $(id).find(".delete").remove();
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

var render_img = function(data, type, full, meta) {
    return '<img src="' + data + '" width="40"></img>';
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
            console.log(jqXHR["responseJSON"]["detail"])
            $("#errorModalDetailText").text(jqXHR["responseJSON"]["detail"]);
            $("#errorModal").modal("show");
        }
    });
}

function loadInventory(serial) {
    url = "/inventory/detail/" + serial
    $.ajax({
        method: 'GET',
        url: url,
        success: function(data) {
            $("#InventoryItems").append(data);
        },
        error: function(jqXHR, textStatus, errorThrown) {
            // do nothing
        }
    });
}