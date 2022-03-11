/* Generate the concentration plot using d3 library. */
function draw_concentration_plot(svg_id, times, concentrations, cumulative_doses, exposed_presence_intervals, short_range_intervals) {

    var time_format = d3.timeFormat('%H:%M');

    var data_for_graphs = {
        'concentrations': [],
        'cumulative_doses': [],
    }
    times.map((time, index) => data_for_graphs.concentrations.push({ 'time': time, 'hour': new Date().setHours(Math.trunc(time), (time - Math.trunc(time)) * 60), 'concentration': concentrations[index]}));
    times.map((time, index) => data_for_graphs.cumulative_doses.push({ 'time': time, 'hour': new Date().setHours(Math.trunc(time), (time - Math.trunc(time)) * 60), 'concentration': cumulative_doses[index]}));

    // Add main SVG element
    var plot_div = document.getElementById(svg_id);
    var vis = d3.select(plot_div).append('svg');

    // H:M time format for x axis.
    xRange = d3.scaleTime().domain([data_for_graphs.concentrations[0].hour, data_for_graphs.concentrations[data_for_graphs.concentrations.length - 1].hour]),
    xTimeRange = d3.scaleLinear().domain([data_for_graphs.concentrations[0].time, data_for_graphs.concentrations[data_for_graphs.concentrations.length - 1].time]),
    bisecHour = d3.bisector((d) => { return d.hour; }).left,

    yRange = d3.scaleLinear().domain([0., Math.max(...concentrations)]),
    yCumulativeRange = d3.scaleLinear().domain([0., Math.max(...cumulative_doses)*1.1]),

    xAxis = d3.axisBottom(xRange).tickFormat(d => time_format(d)),
    yAxis = d3.axisLeft(yRange).ticks(4),
    yCumulativeAxis = d3.axisRight(yCumulativeRange).ticks(4);

    // Line representing the mean concentration.
    var lineFunc = d3.line();
    var draw_line = vis.append('svg:path')
        .attr('stroke', '#1f77b4')
        .attr('stroke-width', 2)
        .attr('fill', 'none');

    var lineCumulative = d3.line();
    var draw_cumulative_line = vis.append('svg:path')
        .attr('stroke', '#1f77b4')
        .attr('stroke-width', 2)
        .style("stroke-dasharray", "5 5")
        .attr('fill', 'none');

    // Area representing the presence of exposed person(s).
    var exposedArea = {};
    var drawArea = {};
    exposed_presence_intervals.forEach((b, index) => {
        exposedArea[index] = d3.area();
        drawArea[index] = vis.append('svg:path')
            .attr('fill', '#1f77b4')
            .attr('fill-opacity', '0.1');
    });

    // Area representing the short range interaction(s).
    var shortRangeArea = {};
    var drawShortRangeArea = {};
    short_range_intervals.forEach((b, index) => {
        shortRangeArea[index] = d3.area();
        drawShortRangeArea[index] = vis.append('svg:path')
            .attr('fill', '#1f00b4')
            .attr('fill-opacity', '0.1');
    });

    // X axis declaration.
    var xAxisEl = vis.append('svg:g')
        .attr('class', 'x axis');

    // X axis label.
    var xAxisLabelEl = vis.append('text')
        .attr('class', 'x label')
        .attr('fill', 'black')
        .attr('text-anchor', 'middle')
        .text('Time of day')

    // Y axis declaration.
    var yAxisEl = vis.append('svg:g')
        .attr('class', 'y axis');

    // Y axis label.
    var yAxisLabelEl = vis.append('svg:text')
        .attr('class', 'y label')
        .attr('fill', 'black')
        .attr('text-anchor', 'middle')
        .text('Mean concentration (virions/m³)');

    // Y cumulative concentration axis declaration.
    var yAxisCumEl = vis.append('svg:g')
        .attr('class', 'y axis')
        .style('font-size', 14)
        .style("stroke-dasharray", "5 5");

    // Y cumulated concentration axis label.
    var yAxisCumLabelEl = vis.append('svg:text')
        .attr('class', 'y label')
        .attr('fill', 'black')
        .attr('text-anchor', 'middle')
        .text('Mean cumulative dose (infectious virus)');

    // Legend for the plot elements - line and area.
    var legendLineIcon = vis.append('rect')
        .attr('width', 20)
        .attr('height', 3)
        .style('fill', '#1f77b4');

    var legendCumulativeIcon = vis.append('line')
        .style("stroke-dasharray", "5 5") //dashed array for line
        .attr('stroke-width', '2')
        .style("stroke", '#1f77b4');

    var legendAreaIcon = vis.append('rect')
        .attr('width', 20)
        .attr('height', 15)
        .attr('fill', '#1f77b4')
        .attr('fill-opacity', '0.1');

    var legendShortRangeAreaIcon = vis.append('rect')
        .attr('width', 20)
        .attr('height', 15)
        .attr('fill', '#1f00b4')
        .attr('fill-opacity', '0.1');

    var legendLineText = vis.append('text')
        .text('Mean concentration')
        .style('font-size', '15px')
        .attr('alignment-baseline', 'central');

    var legendCumutiveText = vis.append('text')
        .text('Cumulative dose')
        .style('font-size', '15px')
        .attr('alignment-baseline', 'central');

    var legendAreaText = vis.append('text')
        .text('Presence of exposed person(s)')
        .style('font-size', '15px')
        .attr('alignment-baseline', 'central');

    var legendShortRangeText = vis.append('text')
        .text('Short range interaction(s)')
        .style('font-size', '15px')
        .attr('alignment-baseline', 'central');

    // Legend bounding
    var legendBBox = vis.append('rect')
        .attr('width', 255)
        .attr('height', 90)
        .attr('stroke', 'lightgrey')
        .attr('stroke-width', '2')
        .attr('rx', '5px')
        .attr('ry', '5px')
        .attr('stroke-linejoin', 'round')
        .attr('fill', 'none');

    // Tooltip.
    var focus = {}, tooltip_rect = {}, tooltip_time = {}, tooltip_concentration = {}, toolBox = {};
    for (const [concentration, data] of Object.entries(data_for_graphs)) {

        focus[concentration] = vis.append('svg:g')
            .style('display', 'none');

        focus[concentration].append('circle')
            .attr('r', 3);

        tooltip_rect[concentration] = focus[concentration].append('rect')
            .attr('fill', 'white')
            .attr('stroke', '#000')
            .attr('width', 85)
            .attr('height', 50)
            .attr('x', 10)
            .attr('y', -22)
            .attr('rx', 4)
            .attr('ry', 4);

        tooltip_time[concentration] = focus[concentration].append('text')
            .attr('id', 'tooltip-time')
            .attr('x', 18)
            .attr('y', -2);

        tooltip_concentration[concentration] = focus[concentration].append('text')
            .attr('id', 'tooltip-concentration')
            .attr('x', 18)
            .attr('y', 18);

        toolBox[concentration] = vis.append('rect')
            .attr('fill', 'none')
            .attr('pointer-events', 'all')
            .on('mouseover', () => { for (const [concentration, data] of Object.entries(focus)) focus[concentration].style('display', null); })
            .on('mouseout', () => { for (const [concentration, data] of Object.entries(focus)) focus[concentration].style('display', 'none'); })
            .on('mousemove', mousemove);
    }

    var graph_width;
    var graph_height;

    function redraw() {

        // Define width and height according to the screen size.
        var div_width = plot_div.clientWidth;
        var div_height = plot_div.clientHeight;
        graph_width = div_width;
        graph_height = div_height
        if (div_width >= 900) { // For screens with width > 900px legend can be on the graph's right side.
            var margins = { top: 30, right: 20, bottom: 50, left: 60 };
            div_width = 900;
            graph_width = div_width * (2/3);
            const svg_margins = {'margin-left': '0rem', 'margin-top': '0rem'};
            Object.entries(svg_margins).forEach(([prop,val]) => vis.style(prop,val));
        }
        else {
            var margins = { top: 30, right: 20, bottom: 50, left: 40 };
            div_width = div_width * 1.1
            graph_width = div_width * .9;
            graph_height = div_height * 0.65; // On mobile screen sizes we want the legend to be on the bottom of the graph.
            const svg_margins = {'margin-left': '-1rem', 'margin-top': '3rem'};
            Object.entries(svg_margins).forEach(([prop,val]) => vis.style(prop,val));
        };

        // Use the extracted size to set the size of the SVG element.
        vis.attr("width", div_width)
            .attr('height', div_height);

        // SVG components according to the width and height.

        // Axis ranges.
        xRange.range([margins.left, graph_width - margins.right]);
        xTimeRange.range([margins.left, graph_width - margins.right]);
        yRange.range([graph_height - margins.bottom, margins.top]);
        yCumulativeRange.range([graph_height - margins.bottom, margins.top]);

        // Line.
        lineFunc.defined(d => !isNaN(d.concentration))
            .x(d => xTimeRange(d.time))
            .y(d => yRange(d.concentration));
        draw_line.attr("d", lineFunc(data_for_graphs.concentrations));

        // Cumulative line.
        lineCumulative.defined(d => !isNaN(d.concentration))
            .x(d => xTimeRange(d.time))
            .y(d => yCumulativeRange(d.concentration));
        draw_cumulative_line.attr("d", lineCumulative(data_for_graphs.cumulative_doses));

        // Area.
        exposed_presence_intervals.forEach((b, index) => {
            exposedArea[index].x(d => xTimeRange(d.time))
                .y0(graph_height - margins.bottom)
                .y1(d => yRange(d.concentration));
    
            drawArea[index].attr('d', exposedArea[index](data_for_graphs.concentrations.filter(d => {
                    return d.time >= b[0] && d.time <= b[1]
            })));
        });

        // Short Range Area.
        short_range_intervals.forEach((b, index) => {
            shortRangeArea[index].x(d => xTimeRange(d.time))
                .y0(graph_height - margins.bottom)
                .y1(d => yRange(d.concentration));

            drawShortRangeArea[index].attr('d', shortRangeArea[index](data_for_graphs.concentrations.filter(d => {
                return d.time >= b[0] && d.time <= b[1]
            })))
        })

        // Axis.
        var xAxis = d3.axisBottom(xRange).tickFormat(d => time_format(d));
        var yAxis = d3.axisLeft(yRange);

        xAxisEl.attr('transform', 'translate(0,' + (graph_height - margins.bottom) + ')')
            .call(xAxis);
        xAxisLabelEl.attr('x', (graph_width + margins.right) / 2)
            .attr('y', graph_height * 0.97);

        yAxisEl.attr('transform', 'translate(' + margins.left + ',0)').call(yAxis);
        yAxisLabelEl.attr('x', (graph_height * 0.9 + margins.bottom) / 2)
            .attr('y', (graph_height + margins.left) * 0.9)
            .attr('transform', 'rotate(-90, 0,' + graph_height + ')');

        yAxisCumEl.attr('transform', 'translate(' + (graph_width - margins.right) + ',0)').call(yCumulativeAxis);
        yAxisCumLabelEl.attr('transform', 'rotate(-90, 0,' + graph_height + ')')
            .attr('x', (graph_height + margins.bottom) / 2);

        if (plot_div.clientWidth >= 900) {
            yAxisCumLabelEl.attr('transform', 'rotate(-90, 0,' + graph_height + ')')
                .attr('x', (graph_height + margins.bottom) / 2)
                .attr('y', 1.71 * graph_width);
        }
        else {
            yAxisCumLabelEl.attr('transform', 'rotate(-90, 0,' + graph_height + ')')
                .attr('x', (graph_height + margins.bottom * 0.55) / 2)
                .attr('y', graph_width + 290);
        }

        // Legend on right side.
        const size = 20;
        if (plot_div.clientWidth >= 900) {
            legendLineIcon.attr('x', graph_width + size * 2.5)
                .attr('y', margins.top + size);
            legendLineText.attr('x', graph_width + 4 * size)
                .attr('y', margins.top + size);
            
            legendCumulativeIcon.attr("x1", graph_width + size + 30)
                .attr("x2", graph_width + 2 * size + 32)
                .attr("y1", 3.5 * size)
                .attr("y2", 3.5 * size);
            legendCumutiveText.attr('x', graph_width + 2.5 * size + 30)
                .attr('y', margins.top + 2 * size);
            
            legendAreaIcon.attr('x', graph_width + size * 2.5)
                .attr('y', margins.top + 2.6 * size);
            legendAreaText.attr('x', graph_width + 4 * size)
                .attr('y', margins.top + 3 * size);
            
            legendShortRangeAreaIcon.attr('x', graph_width + size * 2.5)
                .attr('y', margins.top + 3.6 * size);
            legendShortRangeText.attr('x', graph_width + 4 * size)
                .attr('y', margins.top + 4 * size);
            
            legendBBox.attr('x', graph_width * 1.07)
                .attr('y', margins.top * 1.2);
        }
        // Legend on the bottom.
        else {
            legendLineIcon.attr('x', size * 0.5)
                .attr('y', graph_height * 1.05);
            legendLineText.attr('x', 2 * size)
                .attr('y', graph_height * 1.05);

            legendCumulativeIcon.attr("x1", size * 0.5)
                .attr("x2", size * 1.55)
                .attr("y1", graph_height * 1.05 + size)
                .attr("y2", graph_height * 1.05 + size);
            legendCumutiveText.attr('x', 2 * size)
                .attr('y', graph_height + 1.65 * size);

            legendAreaIcon.attr('x', size * 0.50)
                .attr('y', graph_height * 1.09 + size);
            legendAreaText.attr('x', 2 * size)
                .attr('y', graph_height + 2.6 * size);

            legendShortRangeAreaIcon.attr('x', size * 0.50)
                .attr('y', graph_height * 1.175 + size);
            legendShortRangeText.attr('x', 2 * size)
                .attr('y', graph_height + 3.65 * size);

            legendBBox.attr('x', 1)
                .attr('y', graph_height);
        }
        
        // ToolBox.
        for (const [concentration, data] of Object.entries(data_for_graphs)) {
            toolBox[concentration].attr('width', graph_width - margins.right)
                .attr('height', graph_height);
        }
    }

    // Draw for the first time to initialize.
    redraw();

    function mousemove() {
        for (const [scenario, data] of Object.entries(data_for_graphs)) {
            if (d3.pointer(event)[0] < graph_width / 2) {
                tooltip_rect[scenario].attr('x', 10)
                tooltip_time[scenario].attr('x', 18)
                tooltip_concentration[scenario].attr('x', 18);
            }
            else {
                tooltip_rect[scenario].attr('x', -90)
                tooltip_time[scenario].attr('x', -82)
                tooltip_concentration[scenario].attr('x', -82)
            }
        }
        // Concentration line
        var x0 = xRange.invert(d3.pointer(event, this)[0]),
            i = bisecHour(data_for_graphs.concentrations, x0, 1),
            d0 = data_for_graphs.concentrations[i - 1],
            d1 = data_for_graphs.concentrations[i];
        if (d1) {
            var d = x0 - d0.hour > d1.hour - x0 ? d1 : d0;
            focus.concentrations.attr('transform', 'translate(' + xRange(d.hour) + ',' + yRange(d.concentration) + ')');
            focus.concentrations.select('#tooltip-time').text('x = ' + time_format(d.hour));
            focus.concentrations.select('#tooltip-concentration').text('y = ' + d.concentration.toFixed(2));
        }
        // Cumulative line
        var x0 = xRange.invert(d3.pointer(event, this)[0]),
            i = bisecHour(data_for_graphs.cumulative_doses, x0, 1),
            d0 = data_for_graphs.cumulative_doses[i - 1],
            d1 = data_for_graphs.cumulative_doses[i];
        if (d1 && d1.concentration) {
            var d = x0 - d0.hour > d1.hour - x0 ? d1 : d0;
            focus.cumulative_doses.attr('transform', 'translate(' + xRange(d.hour) + ',' + yCumulativeRange(d.concentration) + ')');
            focus.cumulative_doses.select('#tooltip-time').text('x = ' + time_format(d.hour));
            focus.cumulative_doses.select('#tooltip-concentration').text('y = ' + d.concentration.toFixed(2));
        }
    }

    // Redraw based on the new size whenever the browser window is resized.
    window.addEventListener("resize", redraw);

    
}

function draw_plot(svg_id, times, concentrations, short_range_concentrations, cumulative_doses) {

    // Used for controlling the short range interactions 
    let button_full_exposure = document.getElementById("button_full_exposure");
    let button_long_exposure = document.getElementById("button_long_exposure");

    var data_for_graphs = {
        'concentrations': [],
        'short_range_concentrations': [],
        'cumulative_doses': [],
    }
    times.map((time, index) => data_for_graphs.concentrations.push({ 'time': time, 'hour': new Date().setHours(Math.trunc(time), (time - Math.trunc(time)) * 60), 'concentration': concentrations[index]}));
    times.map((time, index) => data_for_graphs.short_range_concentrations.push({ 'time': time, 'hour': new Date().setHours(Math.trunc(time), (time - Math.trunc(time)) * 60), 'concentration': short_range_concentrations[index]}));
    times.map((time, index) => data_for_graphs.cumulative_doses.push({ 'time': time, 'hour': new Date().setHours(Math.trunc(time), (time - Math.trunc(time)) * 60), 'concentration': cumulative_doses[index]}));

    // Add main SVG element
    var plot_div = document.getElementById(svg_id);
    var vis = d3.select(plot_div).append('svg');

    var time_format = d3.timeFormat('%H:%M');
    // H:M time format for x axis.
    xRange = d3.scaleTime().domain([data_for_graphs.concentrations[0].hour, data_for_graphs.concentrations[data_for_graphs.concentrations.length - 1].hour]),
    xTimeRange = d3.scaleLinear().domain([data_for_graphs.concentrations[0].time, data_for_graphs.concentrations[data_for_graphs.concentrations.length - 1].time]),
    bisecHour = d3.bisector((d) => { return d.hour; }).left,

    yRange = d3.scaleLinear(),
    yCumulativeRange = d3.scaleLinear().domain([0., Math.max(...cumulative_doses)*1.1]),
    
    yAxis = d3.axisLeft();
    yCumulativeAxis = d3.axisRight(yCumulativeRange).ticks(4);

    // X axis declaration.
    var xAxisEl = vis.append('svg:g')
        .attr('class', 'x axis');

    // X axis label.
    var xAxisLabelEl = vis.append('text')
        .attr('class', 'x label')
        .attr('fill', 'black')
        .attr('text-anchor', 'middle')
        .text('Time of day')

    // Y axis declaration.
    var yAxisEl = vis.append('svg:g')
        .attr('class', 'y axis');

    // Y axis label.
    var yAxisLabelEl = vis.append('svg:text')
        .attr('class', 'y label')
        .attr('fill', 'black')
        .attr('text-anchor', 'middle')
        .text('Mean concentration (virions/m³)');

    // Y cumulative concentration axis declaration.
    var yAxisCumEl = vis.append('svg:g')
        .attr('class', 'y axis')
        .style('font-size', 14)
        .style("stroke-dasharray", "5 5");

    // Y cumulated concentration axis label.
    var yAxisCumLabelEl = vis.append('svg:text')
        .attr('class', 'y label')
        .attr('fill', 'black')
        .attr('text-anchor', 'middle')
        .text('Mean cumulative dose (infectious virus)');

    // Legend for the plot elements - line and area.
    var legendLineIcon = vis.append('rect')
        .attr('width', 20)
        .attr('height', 3)
        .style('fill', '#1f77b4');

    var legendCumulativeIcon = vis.append('line')
        .style("stroke-dasharray", "5 5") //dashed array for line
        .attr('stroke-width', '2')
        .style("stroke", '#1f77b4');

    var legendAreaIcon = vis.append('rect')
        .attr('width', 20)
        .attr('height', 15)
        .attr('fill', '#1f77b4')
        .attr('fill-opacity', '0.1');

    if (button_full_exposure || button_long_exposure) {
        var legendShortRangeAreaIcon = vis.append('rect')
            .attr('width', 20)
            .attr('height', 15)
            .attr('fill', '#1f00b4')
            .attr('fill-opacity', '0.1');
    }

    var legendLineText = vis.append('text')
        .text('Mean concentration')
        .style('font-size', '15px')
        .attr('alignment-baseline', 'central');

    var legendCumutiveText = vis.append('text')
        .text('Cumulative dose')
        .style('font-size', '15px')
        .attr('alignment-baseline', 'central');

    var legendAreaText = vis.append('text')
        .text('Presence of exposed person(s)')
        .style('font-size', '15px')
        .attr('alignment-baseline', 'central');

    if (button_full_exposure || button_long_exposure) {
        var legendShortRangeText = vis.append('text')
            .text('Short range interaction(s)')
            .style('font-size', '15px')
            .attr('alignment-baseline', 'central');
    }

    // Legend bounding
    if (button_full_exposure || button_long_exposure) legendBBox_height = 90;
    else legendBBox_height = 68;
    var legendBBox = vis.append('rect')
        .attr('width', 255)
        .attr('height', legendBBox_height)
        .attr('stroke', 'lightgrey')
        .attr('stroke-width', '2')
        .attr('rx', '5px')
        .attr('ry', '5px')
        .attr('stroke-linejoin', 'round')
        .attr('fill', 'none');

    // Line representing the mean concentration.
    var lineFunc = d3.line();
    var draw_line = vis.append('g')
        .attr('clip-path', 'url(#clip)');
    draw_line.append('svg:path')
        .attr('class', 'line')
        .attr('stroke', '#1f77b4')
        .attr('stroke-width', 2)
        .attr('fill', 'none');
    
    // Line representing the cumulative concentration.
    var lineCumulative = d3.line();
    var draw_cumulative_line = vis.append('svg:path')
        .attr('stroke', '#1f77b4')
        .attr('stroke-width', 2)
        .style("stroke-dasharray", "5 5")
        .attr('fill', 'none');

    // Area representing the presence of exposed person(s).
    var exposedArea = {};
    var drawArea = {};
    exposed_presence_intervals.forEach((b, index) => {
        exposedArea[index] = d3.area();
        drawArea[index] = draw_line.append('svg:path')
            .attr('fill', '#1f77b4')
            .attr('fill-opacity', '0.1');
    });

    // Area representing the short range interaction(s).
    var shortRangeArea = {};
    var drawShortRangeArea = {};
    short_range_intervals.forEach((b, index) => {
        shortRangeArea[index] = d3.area();
        drawShortRangeArea[index] = draw_line.append('svg:path')
            .attr('fill', '#1f00b4')
            .attr('fill-opacity', '0.1');
    });

    var clip = vis.append("defs").append("svg:clipPath")
        .attr("id", "clip")
        .append("svg:rect")
        .attr("x", 0)
        .attr("y", 30);

    var brush = d3.brushY();

    function update_concentration_plot(data, long_range_data, data_for_graphs) {
        yRange.domain([0., Math.max(...data)]);
        yAxisEl.transition().duration(1000).call(yAxis);
       
        lineFunc.defined(d => !isNaN(d.concentration))
            .x(d => xTimeRange(d.time))
            .y(d => yRange(d.concentration));
        draw_line.select('.line')
            .enter()
            .merge(draw_line.select('.line'))
            .transition()
            .duration(1000)
            .attr("d", lineFunc(long_range_data));

        // Area.
        exposed_presence_intervals.forEach((b, index) => {
            exposedArea[index].x(d => xTimeRange(d.time))
                .y0(graph_height - 50)
                .y1(d => yRange(d.concentration)
            );
            drawArea[index].transition().duration(1000).attr('d', exposedArea[index](long_range_data.filter(d => {
                    return d.time >= b[0] && d.time <= b[1]
            })));
        });

        // Short Range Area.
        short_range_intervals.forEach((b, index) => {
            shortRangeArea[index].x(d => xTimeRange(d.time))
                .y0(graph_height - 50)
                .y1(d => yRange(d.concentration));

            drawShortRangeArea[index].transition().duration(1000).attr('d', shortRangeArea[index](long_range_data.filter(d => {
                return d.time >= b[0] && d.time <= b[1]
            })));
        });

        brush.on("end", updateChart); // Each time the brush selection changes, trigger the 'updateChart' function
        
        // Brushing
        draw_line.append("svg:g")
            .attr("class", "brush")
            .call(brush);

        // A function that set idleTimeOut to null
        var idleTimeout
        function idled() { idleTimeout = null; }

        // A function that updates the chart for given boundaries
        function updateChart(event,d) {
            // What are the selected boundaries?
            extent = event.selection

            // If no selection, back to initial coordinate. Otherwise, update Y axis domain
            if(!extent) {
                if (!idleTimeout) return idleTimeout = setTimeout(idled, 350); // This allows to wait a little bit
            } 
            else {
                yRange.domain([ yRange.invert(extent[1]), yRange.invert(extent[0]) ])
                draw_line.select(".brush").call(brush.move, null) // This remove the grey brush area as soon as the selection has been done
            }

            // Update axis and line position
            yAxisEl.transition().duration(1000).call(d3.axisLeft(yRange))
            lineFunc.defined(d => !isNaN(d.concentration))
                .x(d => xTimeRange(d.time))
                .y(d => yRange(d.concentration));
            draw_line
                .select('.line')
                .transition()
                .duration(1000)
                .attr("d", lineFunc(data_for_graphs));

            // Area.
            exposed_presence_intervals.forEach((b, index) => {
                exposedArea[index].x(d => xTimeRange(d.time))
                    .y0(graph_height - 50)
                    .y1(d => yRange(d.concentration));
                drawArea[index].transition().duration(1000).attr('d', exposedArea[index](data_for_graphs.filter(d => {
                        return d.time >= b[0] && d.time <= b[1]
                })));
            });

            // Short Range Area.
            short_range_intervals.forEach((b, index) => {
                shortRangeArea[index].x(d => xTimeRange(d.time))
                    .y0(graph_height - 50)
                    .y1(d => yRange(d.concentration));

                drawShortRangeArea[index].transition().duration(1000).attr('d', shortRangeArea[index](data_for_graphs.filter(d => {
                    return d.time >= b[0] && d.time <= b[1]
                })));
            });
        }
    }

    function redraw() {

        // Define width and height according to the screen size.
        var div_width = plot_div.clientWidth;
        var div_height = plot_div.clientHeight;
        graph_width = div_width;
        graph_height = div_height
        if (div_width >= 900) { // For screens with width > 900px legend can be on the graph's right side.
            var margins = { top: 30, right: 20, bottom: 50, left: 60 };
            div_width = 900;
            graph_width = div_width * (2/3);
            const svg_margins = {'margin-left': '0rem', 'margin-top': '0rem'};
            Object.entries(svg_margins).forEach(([prop,val]) => vis.style(prop,val));
        }
        else {
            var margins = { top: 30, right: 20, bottom: 50, left: 40 };
            div_width = div_width * 1.1
            graph_width = div_width * .9;
            graph_height = div_height * 0.65; // On mobile screen sizes we want the legend to be on the bottom of the graph.
            const svg_margins = {'margin-left': '-1rem', 'margin-top': '3rem'};
            Object.entries(svg_margins).forEach(([prop,val]) => vis.style(prop,val));
        };

        // Use the extracted size to set the size of the SVG element.
        vis.attr("width", div_width)
            .attr('height', div_height);

        // SVG components according to the width and height.

        // clipPath: everything out of this area won't be drawn.
        clip.attr("width", graph_width - margins.right)
            .attr("height", graph_height - margins.top - margins.bottom);

        // Add brushing
        brush.extent([[margins.left, margins.top],[graph_width - margins.right, graph_height - margins.bottom ]]);
        
        // Axis ranges.
        xRange.range([margins.left, graph_width - margins.right]);
        xTimeRange.range([margins.left, graph_width - margins.right]);
        yRange.range([graph_height - margins.bottom, margins.top]);
        yCumulativeRange.range([graph_height - margins.bottom, margins.top]);

        // Axis.
        var xAxis = d3.axisBottom(xRange).tickFormat(d => time_format(d));
        yAxis.scale(yRange);

        xAxisEl.attr('transform', 'translate(0,' + (graph_height - margins.bottom) + ')')
            .call(xAxis);
        xAxisLabelEl.attr('x', (graph_width + margins.right) / 2)
            .attr('y', graph_height * 0.97);
        
        yAxisEl.attr('transform', 'translate(' + margins.left + ',0)');
        yAxisLabelEl.attr('x', (graph_height * 0.9 + margins.bottom) / 2)
            .attr('y', (graph_height + margins.left) * 0.9)
            .attr('transform', 'rotate(-90, 0,' + graph_height + ')');

        yAxisCumEl.attr('transform', 'translate(' + (graph_width - margins.right) + ',0)').call(yCumulativeAxis);
        yAxisCumLabelEl.attr('transform', 'rotate(-90, 0,' + graph_height + ')')
            .attr('x', (graph_height + margins.bottom) / 2);

        if (plot_div.clientWidth >= 900) {
            yAxisCumLabelEl.attr('transform', 'rotate(-90, 0,' + graph_height + ')')
                .attr('x', (graph_height + margins.bottom) / 2)
                .attr('y', 1.71 * graph_width);
        }
        else {
            yAxisCumLabelEl.attr('transform', 'rotate(-90, 0,' + graph_height + ')')
                .attr('x', (graph_height + margins.bottom * 0.55) / 2)
                .attr('y', graph_width + 290);
        }

        // Legend on right side.
        const size = 20;
        if (plot_div.clientWidth >= 900) {
            legendLineIcon.attr('x', graph_width + size * 2.5)
                .attr('y', margins.top + size);
            legendLineText.attr('x', graph_width + 4 * size)
                .attr('y', margins.top + size);
            
            legendCumulativeIcon.attr("x1", graph_width + size + 30)
                .attr("x2", graph_width + 2 * size + 32)
                .attr("y1", 3.5 * size)
                .attr("y2", 3.5 * size);
            legendCumutiveText.attr('x', graph_width + 2.5 * size + 30)
                .attr('y', margins.top + 2 * size);
            
            legendAreaIcon.attr('x', graph_width + size * 2.5)
                .attr('y', margins.top + 2.6 * size);
            legendAreaText.attr('x', graph_width + 4 * size)
                .attr('y', margins.top + 3 * size);
            
            if (button_full_exposure || button_long_exposure) {
                legendShortRangeAreaIcon.attr('x', graph_width + size * 2.5)
                    .attr('y', margins.top + 3.6 * size);
                legendShortRangeText.attr('x', graph_width + 4 * size)
                    .attr('y', margins.top + 4 * size);
            }
            
            legendBBox.attr('x', graph_width * 1.07)
                .attr('y', margins.top * 1.2);
        }
        // Legend on the bottom.
        else {
            legendLineIcon.attr('x', size * 0.5)
                .attr('y', graph_height * 1.05);
            legendLineText.attr('x', 2 * size)
                .attr('y', graph_height * 1.05);

            legendCumulativeIcon.attr("x1", size * 0.5)
                .attr("x2", size * 1.55)
                .attr("y1", graph_height * 1.05 + size)
                .attr("y2", graph_height * 1.05 + size);
            legendCumutiveText.attr('x', 2 * size)
                .attr('y', graph_height + 1.65 * size);

            legendAreaIcon.attr('x', size * 0.50)
                .attr('y', graph_height * 1.09 + size);
            legendAreaText.attr('x', 2 * size)
                .attr('y', graph_height + 2.6 * size);

            if (button_full_exposure || button_long_exposure) {
                legendShortRangeAreaIcon.attr('x', size * 0.50)
                    .attr('y', graph_height * 1.175 + size);
                legendShortRangeText.attr('x', 2 * size)
                    .attr('y', graph_height + 3.65 * size);
            }

            legendBBox.attr('x', 1)
                .attr('y', graph_height);
        }

        // Cumulative line.
        lineCumulative.defined(d => !isNaN(d.concentration))
            .x(d => xTimeRange(d.time))
            .y(d => yCumulativeRange(d.concentration));
        draw_cumulative_line.attr("d", lineCumulative(data_for_graphs.cumulative_doses));
    }

    if (button_full_exposure) {
        button_full_exposure.addEventListener("click", () => {
            update_concentration_plot(short_range_concentrations, data_for_graphs.short_range_concentrations, data_for_graphs.short_range_concentrations);
        });
    }
    if (button_long_exposure) {
        button_long_exposure.addEventListener("click", () => {
            update_concentration_plot(concentrations, data_for_graphs.short_range_concentrations, data_for_graphs.concentrations);
        });
    }

    // If user double click, reinitialize the chart
    vis.on("dblclick",function(){
        yRange.domain([0., Math.max(...short_range_concentrations)])
        yAxisEl.transition().call(d3.axisLeft(yRange))
        lineFunc.defined(d => !isNaN(d.concentration))
            .x(d => xTimeRange(d.time))
            .y(d => yRange(d.concentration));
        draw_line
          .select('.line')
          .transition()
          .attr("d", lineFunc(data_for_graphs.short_range_concentrations));
        exposed_presence_intervals.forEach((b, index) => {
            exposedArea[index].x(d => xTimeRange(d.time))
                .y0(graph_height - 50)
                .y1(d => yRange(d.concentration)
            );
            drawArea[index].transition().duration(1000).attr('d', exposedArea[index](data_for_graphs.short_range_concentrations.filter(d => {
                    return d.time >= b[0] && d.time <= b[1]
            })));
        });
        short_range_intervals.forEach((b, index) => {
            shortRangeArea[index].x(d => xTimeRange(d.time))
                .y0(graph_height - 50)
                .y1(d => yRange(d.concentration));

            drawShortRangeArea[index].transition().duration(1000).attr('d', shortRangeArea[index](data_for_graphs.short_range_concentrations.filter(d => {
                return d.time >= b[0] && d.time <= b[1]
            })));
        });
    });

    // Draw for the first time to initialize.
    redraw();
    update_concentration_plot(short_range_concentrations, data_for_graphs.short_range_concentrations, data_for_graphs.short_range_concentrations);

    // Redraw based on the new size whenever the browser window is resized.
    window.addEventListener("resize", redraw);

}


// Generate the alternative scenarios plot using d3 library.
// 'alternative_scenarios' is a dictionary with all the alternative scenarios 
// 'times' is a list of times for all the scenarios
function draw_alternative_scenarios_plot(concentration_plot_svg_id, alternative_plot_svg_id, times, alternative_scenarios) {
     // H:M format
    var time_format = d3.timeFormat('%H:%M');
    // D3 array of ten categorical colors represented as RGB hexadecimal strings.
    var colors = d3.schemeAccent;

    // Variable for the highest concentration for all the scenarios
    var highest_concentration = 0.

    var data_for_scenarios = {}
    for (scenario in alternative_scenarios) {
        scenario_concentrations = alternative_scenarios[scenario].concentrations

        highest_concentration = Math.max(highest_concentration, Math.max(...scenario_concentrations))

        var data = []
        times.map((time, index) => data.push({ 'time': time, 'hour': new Date().setHours(Math.trunc(time), (time - Math.trunc(time)) * 60), 'concentration': scenario_concentrations[index] }))

        // Add data into lines dictionary
        data_for_scenarios[scenario] = data
    }

    // We need one scenario to get the time range
    var first_scenario = Object.values(data_for_scenarios)[0]

    // Add main SVG element
    var alternative_plot_div = document.getElementById(alternative_plot_svg_id);
    var vis = d3.select(alternative_plot_div).append('svg');

    var xRange = d3.scaleTime().domain([first_scenario[0].hour, first_scenario[first_scenario.length - 1].hour]);
    var xTimeRange = d3.scaleLinear().domain([times[0], times[times.length - 1]]);
    var bisecHour = d3.bisector((d) => { return d.hour; }).left;

    var yRange = d3.scaleLinear().domain([0., highest_concentration]);

    // Line representing the mean concentration for each scenario.
    var lineFuncs = {}, draw_lines  = {}, label_icons = {}, label_text = {};
    for (const [scenario_name, data] of Object.entries(data_for_scenarios)) {
        var scenario_index = Object.keys(data_for_scenarios).indexOf(scenario_name)

        // Line representing the mean concentration.
        lineFuncs[scenario_name] = d3.line();

        draw_lines[scenario_name] = vis.append('svg:path')
            .attr("stroke", colors[scenario_index])
            .attr('stroke-width', 2)
            .attr('fill', 'none');

        // Legend for the plot elements - lines.
        label_icons[scenario_name] = vis.append('rect')
            .attr('width', 20)
            .attr('height', 3)
            .style('fill', colors[scenario_index]);

        label_text[scenario_name] = vis.append('text')
            .text(scenario_name)
            .style('font-size', '15px')
            .attr('alignment-baseline', 'central');

    }
    
    // X axis.
    var xAxisEl = vis.append('svg:g')
        .attr('class', 'x axis');

    // X axis label.
    var xAxisLabelEl = vis.append('text')
        .attr('class', 'x label')
        .attr('fill', 'black')
        .attr('text-anchor', 'middle')
        .text('Time of day');

    // Y axis declaration.
    var yAxisEl = vis.append('svg:g')
         .attr('class', 'y axis');

    // Y axis label.
    var yAxisLabelEl = vis.append('svg:text')
        .attr('class', 'y label')
        .attr('fill', 'black')
        .attr('text-anchor', 'middle')
        .text('Mean concentration (virions/m³)');

    // Legend bounding box.
    var legendBBox = vis.append('rect')
        .attr('width', 275)
        .attr('height', 25 * (Object.keys(data_for_scenarios).length))
        .attr('stroke', 'lightgrey')
        .attr('stroke-width', '2')
        .attr('rx', '5px')
        .attr('ry', '5px')
        .attr('stroke-linejoin', 'round')
        .attr('fill', 'none');

    // Tooltip.
    var focus = {}, tooltip_rect = {}, tooltip_time = {}, tooltip_concentration = {}, toolBox = {};
    for (const [scenario_name, data] of Object.entries(data_for_scenarios)) {

        focus[scenario_name] = vis.append('svg:g')
            .style('display', 'none');

        focus[scenario_name].append('circle')
            .attr('r', 3);

        tooltip_rect[scenario_name] = focus[scenario_name].append('rect')
            .attr('fill', 'white')
            .attr('stroke', '#000')
            .attr('width', 80)
            .attr('height', 50)
            .attr('y', -22)
            .attr('rx', 4)
            .attr('ry', 4);

        tooltip_time[scenario_name] = focus[scenario_name].append('text')
            .attr('id', 'tooltip-time')
            .attr('y', -2);

        tooltip_concentration[scenario_name] = focus[scenario_name].append('text')
            .attr('id', 'tooltip-concentration')
            .attr('y', 18);

        toolBox[scenario_name] = vis.append('rect')
            .attr('fill', 'none')
            .attr('pointer-events', 'all')
            .on('mouseover', () => { for (const [scenario_name, data] of Object.entries(focus)) focus[scenario_name].style('display', null); })
            .on('mouseout', () => { for (const [scenario_name, data] of Object.entries(focus)) focus[scenario_name].style('display', 'none'); })
            .on('mousemove', mousemove);
    }

    var graph_width;
    var graph_height;

    function redraw() {
        // Define width and height according to the screen size.
        var div_width = document.getElementById(concentration_plot_svg_id).clientWidth;
        var div_height = document.getElementById(concentration_plot_svg_id).clientHeight;
        graph_width = div_width;
        graph_height = div_height
        if (div_width >= 900) { // For screens with width > 900px legend can be on the graph's right side.
            var margins = { top: 30, right: 20, bottom: 50, left: 60 };
            div_width = 900;
            graph_width = div_width * (2/3);
            const svg_margins = {'margin-left': '0rem'};
            Object.entries(svg_margins).forEach(([prop,val]) => vis.style(prop,val));
        }
        else {
            var margins = { top: 30, right: 20, bottom: 50, left: 40 };
            div_width = div_width * 1.1
            graph_width = div_width * .95;
            graph_height = div_height * 0.65; // On mobile screen sizes we want the legend to be on the bottom of the graph.
            const svg_margins = {'margin-left': '-1rem'};
            Object.entries(svg_margins).forEach(([prop,val]) => vis.style(prop,val));
        };

        // Use the extracted size to set the size of the SVG element.
        vis.attr("width", div_width)
            .attr('height', div_height);

        // SVG components according to the width and height.

        // Axis ranges.
        xRange.range([margins.left, graph_width - margins.right]);
        xTimeRange.range([margins.left, graph_width - margins.right]);
        yRange.range([graph_height - margins.bottom, margins.top]);

        for (const [scenario_name, data] of Object.entries(data_for_scenarios)) {
            var scenario_index = Object.keys(data_for_scenarios).indexOf(scenario_name)
            // Lines.
            lineFuncs[scenario_name].defined(d => !isNaN(d.concentration))
                .x(d => xTimeRange(d.time))
                .y(d => yRange(d.concentration));
            draw_lines[scenario_name].attr("d", lineFuncs[scenario_name](data));

            // Legend on right side.
            var size = 20 * (scenario_index + 1);
            if (document.getElementById(concentration_plot_svg_id).clientWidth >= 900) {
                label_icons[scenario_name].attr('x', graph_width + 20)
                    .attr('y', margins.top + size);
                label_text[scenario_name].attr('x', graph_width + 3 * 20)
                    .attr('y', margins.top + size);
            }
            // Legend on the bottom.
            else {
                label_icons[scenario_name].attr('x', margins.left * 0.3)
                    .attr('y', graph_height + size);
                label_text[scenario_name].attr('x', margins.left * 1.4)
                    .attr('y', graph_height + size);
            }

        }

        // Axis.
        var xAxis = d3.axisBottom(xRange).tickFormat(d => time_format(d));
        var yAxis = d3.axisLeft(yRange);

        xAxisEl.attr('transform', 'translate(0,' + (graph_height - margins.bottom) + ')')
            .call(xAxis);
        xAxisLabelEl.attr('x', (graph_width + margins.right) / 2)
            .attr('y', graph_height * 0.97)

        yAxisEl.attr('transform', 'translate(' + margins.left + ',0)')
            .call(yAxis);
        yAxisLabelEl.attr('transform', 'rotate(-90, 0,' + graph_height + ')')
            .attr('x', (graph_height * 0.9 + margins.bottom) / 2)
            .attr('y', (graph_height + margins.left) * 0.90);

        // Legend on right side.
        if (document.getElementById(concentration_plot_svg_id).clientWidth >= 900) {
            legendBBox.attr('x', graph_width * 1.02)
                .attr('y', margins.top * 1.15);
            
        }
        // Legend on the bottom.
        else {
            legendBBox.attr('x', 1)
                .attr('y', graph_height * 1.02)
        }

        // ToolBox.
        for (const [scenario_name, data] of Object.entries(data_for_scenarios)) {
            toolBox[scenario_name].attr('width', graph_width - margins.right)
                .attr('height', graph_height);
        }
    }

    // Draw for the first time to initialize.
    redraw();

    function mousemove() {
        for (const [scenario_name, data] of Object.entries(data_for_scenarios)) {
            if (d3.pointer(event)[0] < graph_width / 2) {
                tooltip_rect[scenario_name].attr('x', 10)
                tooltip_time[scenario_name].attr('x', 18)
                tooltip_concentration[scenario_name].attr('x', 18);
            }
            else {
                tooltip_rect[scenario_name].attr('x', -90)
                tooltip_time[scenario_name].attr('x', -82)
                tooltip_concentration[scenario_name].attr('x', -82)
            }
            var x0 = xRange.invert(d3.pointer(event, this)[0]),
                i = bisecHour(data, x0, 1),
                d0 = data[i - 1],
                d1 = data[i],
                d = x0 - d0.hour > d1.hour - x0 ? d1 : d0;
            focus[scenario_name].attr('transform', 'translate(' + xRange(d.hour) + ',' + yRange(d.concentration) + ')');
            focus[scenario_name].select('#tooltip-time').text('x = ' + time_format(d.hour));
            focus[scenario_name].select('#tooltip-concentration').text('y = ' + d.concentration.toFixed(2));
        }
    }

    // Redraw based on the new size whenever the browser window is resized.
    window.addEventListener("resize", redraw);
}

function copy_clipboard(shareable_link) {

    $("#mobile_link").attr('title', 'Copied!')
          .tooltip('_fixTitle')
          .tooltip('show');
          
    navigator.clipboard.writeText(shareable_link);
}