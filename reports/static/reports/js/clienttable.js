// resize modal content to max windows height
function do_resize() {
    $('#detail_content').height($(window).height() - 340);
}

$(window).resize(do_resize);

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

} );

var current_pathname = "";

function getComputerItem(pathname) {
    if ($('#save_and_cancel').length && !$('#save_and_cancel').hasClass('hidden')) {
        requested_pathname = pathname;
        $("#saveOrCancelConfirmationModal").modal("show");
        event.preventDefault();
        return;
    }
		$("#loadingModal").modal("show");
    var manifestItemURL = '/reports/' + pathname;
    $.ajax({
        method: 'GET',
        url: manifestItemURL,
        timeout: 10000,
        cache: false,
        success: function(data) {
						$('#computer_detail').html(data);
          	//  hideSaveOrCancelBtns();
          	//  detectUnsavedChanges();
            current_pathname = pathname;
            requested_pathname = "";

            window.history.replaceState({'computer_detail': data}, manifestItemURL, '/reports/');
            window.location.hash = pathname;

            if (!$('#computerDetails').hasClass('in')){
							do_resize()
              $("#computerDetails").modal("show");
            }
						$("#loadingModal").modal("hide");
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
						 $("#loadingModal").modal("hide");
        },
        dataType: 'html'
    })
}

function cancelEdit() {
    //$('#cancelEditConfirmationModal').modal('hide');
    $("#computerDetails").modal("hide");
    //$('.modal-backdrop').remove();
    hideSaveOrCancelBtns();
    //getManifestItem(current_pathname);
}
