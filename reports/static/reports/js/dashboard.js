var hardwareChart = ""
var osChart = ""

$(document).ready(function() {
    createOSBreakdown();
    createHardwareBreakdown();

    setInterval (function () {
        //reload charts
        updateCharts();
    }, 5000);
});

function getAjaxData(url, callback) {
    $.ajax({
      type: 'GET',
      url: url,
      dataType: "json",
      contentType: "application/json",
      success: callback
  });
}

function createMorrisData(json) {
  var result = {};
  for(var i = 0; i < json.length; i++){
      for(var item in json[i]){
          if(!result[json[i][item]]){
              result[json[i][item]] = 0;
          }
          result[json[i][item]]++;
      }
  }
  var data = [];
  for(var item in result) {
      dataItems = {}
      dataItems["label"] = item
      dataItems["value"] = result[item]
      data.push(dataItems)
  }
  return data;
}

function createHardwareBreakdown() {
    getAjaxData("/api/report?api_fields=machine_model", function(data){
        var response = data;
        response = createMorrisData(response);
        //console.log(response)
        hardwareChart = Morris.Bar({
            element: 'hardwarebreakdown',
            data: response,
            xkey: 'label',
            ykeys: ['value'],
            labels: ['Count'],
            hideHover: true,
            stacked: true,
            resize: true
        }).on('click', function(i, row){
            window.location.href = "/reports?model="+row.label;
        });
    })
}

function createOSBreakdown() {
    getAjaxData("/api/report?api_fields=os_version", function(data){
        var response = data;
        response = createMorrisData(response);
        //console.log(response)
        osChart = Morris.Donut({
            element: 'osbreakdown',
            data: response,
            resize: true
        }).on('click', function(i, row){
            window.location.href = "/reports?os_version="+row.label;
        });
    })
}

function updateCharts() {
  getAjaxData("/api/report?api_fields=os_version", function(data){
    var response = data;
    response = createMorrisData(response);
    osChart.setData(response);
  })

  getAjaxData("/api/report?api_fields=machine_model", function(data){
    var response = data;
    response = createMorrisData(response);
    hardwareChart.setData(response);
  })
}