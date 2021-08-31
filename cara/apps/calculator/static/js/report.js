/* Generate the concentration plot using d3 library. */
function draw_concentration_plot(svg_id, times, concentrations, exposed_presence_intervals) {
    
    var time_format = d3.timeFormat('%H:%M');

    var data = []
    times.map((time, index) => data.push({'time': time, 'hour': new Date().setHours(Math.trunc(time), (time - Math.trunc(time)) * 60), 'concentration': concentrations[index] }))

    var plot_div = document.getElementById(svg_id);
    
    var height = plot_div.clientHeight;
    var width; // To be defined later

    var vis = d3.select(plot_div).append('svg').attr('height', height);
    
    var margins = { top: 30, right: 20, bottom: 50, left: 50 };

    // H:M time format for x axis.
    var xRange = d3.scaleTime().domain([data[0].hour, data[data.length - 1].hour]);
    var xTimeRange = d3.scaleLinear().domain([data[0].time, data[data.length - 1].time]);
    var bisecHour = d3.bisector((d) => { return d.hour; }).left;

    var yRange = d3.scaleLinear().range([height - margins.bottom, margins.top]).domain([0., Math.max(...concentrations)]);
    var yAxis = d3.axisLeft(yRange);

    // Line representing the mean concentration.
    var lineFunc = d3.line();
    var draw_line = vis.append('svg:path')
        .attr('stroke', '#1f77b4')
        .attr('stroke-width', 2)
        .attr('fill', 'none');

    // Plot tittle.
    var plotTitleEl = vis.append('svg:foreignObject')
        .attr("background-color", "transparent")
        .attr('height', margins.top)
        .style('text-align', 'center')
        .html('<b>Mean concentration of virions</b>');

    // X axis declaration.
    var xAxisEl = vis.append('svg:g')
        .attr('class', 'x axis')
        .attr('transform', 'translate(0,' + (height - margins.bottom) + ')');

    // X axis label.
    var xAxisLabelEl = vis.append('text')
        .attr('class', 'x label')
        .attr('fill', 'black')
        .attr('text-anchor', 'middle')
        .attr('y', height * 0.97)
        .text('Time of day')

    // Y axis declaration.
    vis.append('svg:g')
        .attr('class', 'y axis')
        .attr('transform', 'translate(' + margins.left + ',0)')
        .call(yAxis);

    // Y axis label.
    vis.append('svg:text')
        .attr('class', 'y label')
        .attr('fill', 'black')
        .attr('transform', 'rotate(-90, 0,' + height + ')')
        .attr('text-anchor', 'middle')
        .attr('x', (height + margins.bottom) / 2)
        .attr('y', (height + margins.left) * 0.92)
        .text('Mean concentration (virions/m³)');

    // Area representing the presence of exposed person(s).
    var exposedArea = {};
    var drawArea = {};
    exposed_presence_intervals.forEach((b, index) => {
        exposedArea[index] = d3.area();
        drawArea[index] = vis.append('svg:path')
            .attr('fill', '#1f77b4')
            .attr('fill-opacity', '0.1');
    });

    // Legend for the plot elements - line and area.
    var size = 20
    var legendLineIcon = vis.append('rect')
        .attr('y', margins.top + size)
        .attr('width', 20)
        .attr('height', 3)
        .style('fill', '#1f77b4');

    var legendAreaIcon = vis.append('rect')
        .attr('y', 3 * size)
        .attr('width', 20)
        .attr('height', 20)
        .attr('fill', '#1f77b4')
        .attr('fill-opacity', '0.1');

    var legendLineText = vis.append('text')
        .attr('y', margins.top + size)
        .text('Mean concentration')
        .style('font-size', '15px')
        .attr('alignment-baseline', 'central');

    var legendAreaText = vis.append('text')
        .attr('y', margins.top + 2 * size)
        .text('Presence of exposed person(s)')
        .style('font-size', '15px')
        .attr('alignment-baseline', 'central');

    // Tooltip.
    var focus = vis.append('svg:g')
        .style('display', 'none');

    focus.append('circle')
        .attr('r', 3);

    focus.append('rect')
        .attr('fill', 'white')
        .attr('stroke', '#000')
        .attr('width', 80)
        .attr('height', 50)
        .attr('x', 10)
        .attr('y', -22)
        .attr('rx', 4)
        .attr('ry', 4);

    focus.append('text')
        .attr('id', 'tooltip-time')
        .attr('x', 18)
        .attr('y', -2);

    focus.append('text')
        .attr('id', 'tooltip-concentration')
        .attr('x', 18)
        .attr('y', 18);

    var toolBox = vis.append('rect')
        .attr('fill', 'none')
        .attr('pointer-events', 'all')
        .attr('height', height)
        .on('mouseover', () => { focus.style('display', null); })
        .on('mouseout', () => { focus.style('display', 'none'); })
        .on('mousemove', mousemove);

    function redraw() {

        // Extract the width and height.
        var width = plot_div.clientWidth;
        if (width >= 900) width = 900;

        // Use the extracted size to set the size of the SVG element.
        vis.attr("width", width);
        // Reduce width so that legend elements can be rendered
        width = width * 0.66;

        // Redefine the variables according to the new clientWidth.
        xRange.range([margins.left, width - margins.right]);
        xTimeRange.range([margins.left, width - margins.right]);

        lineFunc.defined(d => !isNaN(d.concentration))
            .x(d => xTimeRange(d.time))
            .y(d => yRange(d.concentration));
        draw_line.attr("d", lineFunc(data));

        plotTitleEl.attr('width', width);

        var xAxis = d3.axisBottom(xRange).tickFormat(d => time_format(d));

        xAxisEl.call(xAxis);
        xAxisLabelEl.attr('x', (width + margins.right) / 2);

        exposed_presence_intervals.forEach((b, index) => {
            exposedArea[index].x(d => xTimeRange(d.time))
                .y0(height - margins.bottom)
                .y1(d => yRange(d.concentration));
    
            drawArea[index].attr('d', exposedArea[index](data.filter(d => {
                    return d.time >= b[0] && d.time <= b[1]
            })));
        });

        legendLineIcon.attr('x', width + size);

        legendAreaIcon.attr('x', width + size);

        legendLineText.attr('x', width + 3 * size);

        legendAreaText.attr('x', width + 3 * size);
            
        toolBox.attr('width', width - margins.right);
    }

    // Draw for the first time to initialize.
    redraw();

    function mousemove() {
        var x0 = xRange.invert(d3.pointer(event, this)[0]),
            i = bisecHour(data, x0, 1),
            d0 = data[i - 1],
            d1 = data[i],
            d = x0 - d0.hour > d1.hour - x0 ? d1 : d0;
        focus.attr('transform', 'translate(' + xRange(d.hour) + ',' + yRange(d.concentration) + ')');
        focus.select('#tooltip-time').text('x = ' + time_format(d.hour));
        focus.select('#tooltip-concentration').text('y = ' + d.concentration.toFixed(2));
    }

    // Redraw based on the new size whenever the browser window is resized.
    window.addEventListener("resize", redraw);

    
}