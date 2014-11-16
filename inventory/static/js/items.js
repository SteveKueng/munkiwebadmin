/*
    This script is used on the inventory/items route to handle loading the
    table data via json. It also formats the columns so each value as clickable
    original version by Joe Wollard; this version by Greg Neagle
*/

$(document).ready(function()
{
    // Perform the json call and format the results so that DataTables will
    // understand it.
    var process_json = function( sSource, aoData, fnCallback )
    {
        $.getJSON( sSource, function(json, status, jqXHR)
        {
            // update the count info badge
            $("#item-count-badge").text(json.length);

            // let datatables do its thing.
            fnCallback( {'aaData': json} );
        });
    }


    var version_count_template = function(name, version, count)
    {
        return "<a href='?name=" + encodeURIComponent(name) 
            + "&version=" + encodeURIComponent(version) + "'>" + version 
            + "<span class='badge badge-info pull-right'>" + count + "</span>"
            + "</a><br />";
    }


    var format_versions_column = function(data, type, rowObject)
    {
        out = ''
        for(var i = 0; i < data.length; i++)
        {
            var version = data[i]['version'],
                count = data[i]['count'];
            out += version_count_template(
                rowObject.name,
                version,
                count
            );
        }
        return out;
    }


    var format_name_column = function(data, type, rowObject)
    {
        return '<a href="?name=' + encodeURIComponent(data)
            + '">' + data + "</a>";
    }


    $("#inventory-items-table").dataTable({
    	"sDom": "<'row'<'col-md-8'i><'col-md-4'f>>t<'row'<'col-md-8'l><'col-md-4'p>>",
        "sAjaxSource": window.location.href + ".json",
        "fnServerData": process_json,
        "sPaginationType": "bootstrap",
        "bStateSave": false,
        "bPaginate": false,
        "aaSorting": [[4,'desc']],
        "sScrollY": ($(window).height() - 235),
        "bScrollInfinite": true,
    	"bScrollCollapse": true,
            "oLanguage": {
      				"sInfo": "_TOTAL_ entries to show.",
      				"sSearch": 'Search' ,
      				"sZeroRecords": "No entries to show",
      				"sInfoFiltered": "(filtering from _MAX_ records)"
    		},
        "aoColumns": [
            {'mData': 'name',
             'mRender': format_name_column
             },
            {'mData': 'versions',
             'mRender': format_versions_column
            }
        ]
    });
});