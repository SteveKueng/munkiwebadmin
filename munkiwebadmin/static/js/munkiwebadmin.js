$(document).ready(function() {
    getRunningMachine();
    setInterval (function () {
        //reload imagr running machine
        getRunningMachine();
    }, 3000);
});

function getRunningMachine() {
    $.ajax({
        method: 'GET',
        url:"/api/report",
        timeout: 10000,
        cache: false,
        success: function(data) {
            // on success
            $(".imagrInprogress").empty()
            var run = 0
            for (var i in data) {
                if(data[i].current_status == "in_progress") {
                    $(".imagrInprogress").prepend('<li><a href="/reports/#'+i+'"><strong>'+data[i].hostname+'</strong><div class="progress"><div class="progress-bar progress-bar-striped progress-bar-animated active" role="progressbar" aria-valuenow="100" aria-valuemin="0" aria-valuemax="100" style="width: 100%"></div></div></a></li>')
                    run++;
                }
                if(run > 4) {
                    break;
                }
                //console.log(JSON.stringify(data[i]));
            }
            if(run > 0) {
                $(".imagrInprogress").append('<li class="divider"></li><li><a href="/reports/?show=inprogress" class="text-center"><strong>See All </strong><i class="fa fa-angle-right"></i></a></li>')
            } else {
                $(".imagrInprogress").append('<li><a class="text-center">no machine in progress</a></li>');
            }
        },
        error: function(jqXHR, textStatus, errorThrown) {
            // on error
        },
    })
}