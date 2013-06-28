google.load('visualization', '1', {'packages':['annotatedtimeline']});
      function drawDateChart() {
        var data = new google.visualization.DataTable();
        data.addColumn('date', 'Date');
        data.addColumn('number', 'Frequency');
        data.addRows([
          {{ timeLineDisplay }}
        ]);
        var TimeLinechart = new google.visualization.AnnotatedTimeLine(document.getElementById("timeline_chart_div"));
        TimeLinechart.draw(data, {displayAnnotations: true});
      }
      
      google.load("visualization", "1", {'packages':["corechart"]});
      
      function drawNetworkChart() {
        var data = google.visualization.arrayToDataTable([
          ['Network', 'Broadcast Frequency'],
          {{ pieChartDisplay }}
        ]);
        var chart = new google.visualization.PieChart(document.getElementById("pie_chart_div"));
        chart.draw(data);//, options);
      }
      
	function addtext() {
		var newtext = document.myform.inputtext.value;
		if (document.myform.placement[1].checked) {
			document.myform.outputtext.value = "";
			}
		document.myform.outputtext.value += newtext;
	}
	
    function getResults() {
    	console.log("hello");
        query = $("#searchButton").val();
      	$.post("/search.html", {"searchterm": search}, function(response){
      		console.log("entered callback");
      	});
	}