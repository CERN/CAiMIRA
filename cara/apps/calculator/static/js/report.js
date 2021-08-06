/* Generate the concentration plot using d3 library. */
function draw_concentration_plot(svg_id, times, concentrations, exposed_presence_intervals) {
    var visBoundingBox = d3.select(svg_id)
        .node()
        .getBoundingClientRect();

    var time_format = d3.timeFormat('%H:%M');

    var data = []
    times.map((time, index) => data.push({ 'time': time, 'hour': new Date().setHours(Math.trunc(time), (time - Math.trunc(time)) * 60), 'concentration': concentrations[index] }))

    var vis = d3.select(svg_id),
        width = visBoundingBox.width - 300,
        height = visBoundingBox.height,
        margins = { top: 30, right: 20, bottom: 50, left: 50 },

        // H:M time format for x axis.
        xRange = d3.scaleTime().range([margins.left, width - margins.right]).domain([data[0].hour, data[data.length - 1].hour]),
        bisecHour = d3.bisector((d) => { return d.hour; }).left,

        yRange = d3.scaleLinear().range([height - margins.bottom, margins.top]).domain([data[0].concentration, data[data.length - 1].concentration]),
        xTimeRange = d3.scaleLinear().range([margins.left, width - margins.right]).domain([data[0].time, data[data.length - 1].time]),

        xAxis = d3.axisBottom(xRange).tickFormat(d => time_format(d)),
        yAxis = d3.axisLeft(yRange);

    // Plot tittle.
    vis.append('svg:foreignObject')
        .attr('width', width)
        .attr('height', margins.top)
        .append('xhtml:body')
        .style('text-align', 'center')
        .html('Mean concentration of infectious quanta');

    // Line representing the mean concentration.
    var lineFunc = d3.line()
        .defined(d => !isNaN(d.concentration))
        .x(d => xTimeRange(d.time))
        .y(d => yRange(d.concentration))
        .curve(d3.curveBasis);

    vis.append('svg:path')
        .attr('d', lineFunc(data))
        .attr('stroke', '#1f77b4')
        .attr('stroke-width', 2)
        .attr('fill', 'none');

    // X axis declaration.
    vis.append('svg:g')
        .attr('class', 'x axis')
        .attr('transform', 'translate(0,' + (height - margins.bottom) + ')')
        .call(xAxis);

    // X axis label.
    vis.append('text')
        .attr('class', 'x label')
        .attr('fill', 'black')
        .attr('text-anchor', 'middle')
        .attr('x', (width + margins.right) / 2)
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
        .text('Mean concentration (q/m^3)');

    // Area representing the presence of exposed person(s).
    exposed_presence_intervals.forEach(b => {
        vis.append('svg:path')
            .attr('d', lineFunc(data.filter(d => {
                return d.time >= b[0] && d.time <= b[1]
            })))
            .attr('fill', 'none');

        var curveFunc = d3.area()
            .x(d => xTimeRange(d.time))
            .y0(height - margins.bottom)
            .y1(d => yRange(d.concentration));

        vis.append('svg:path')
            .attr('d', curveFunc(data.filter(d => {
                return d.time >= b[0] && d.time <= b[1]
            })))
            .attr('fill', '#1f77b4')
            .attr('fill-opacity', '0.1');
    })

    // Legend for the plot elements - line and area.
    var size = 20
    vis.append('rect')
        .attr('x', width + size)
        .attr('y', margins.top + size)
        .attr('width', 20)
        .attr('height', 3)
        .style('fill', '#1f77b4');

    vis.append('rect')
        .attr('x', width + size)
        .attr('y', 3 * size)
        .attr('width', 20)
        .attr('height', 20)
        .attr('fill', '#1f77b4')
        .attr('fill-opacity', '0.1');

    vis.append('text')
        .attr('x', width + 3 * size)
        .attr('y', margins.top + size)
        .text('Mean concentration')
        .style('font-size', '15px')
        .attr('alignment-baseline', 'central');

    vis.append('text')
        .attr('x', width + 3 * size)
        .attr('y', margins.top + 2 * size)
        .text('Presence of exposed person(s)')
        .style('font-size', '15px')
        .attr('alignment-baseline', 'central');

    // Legend bounding box.
    vis.append('rect')
        .attr('width', 275)
        .attr('height', 50)
        .attr('x', width * 1.005)
        .attr('y', margins.top + 5)
        .attr('stroke', 'lightgrey')
        .attr('stroke-width', '2')
        .attr('rx', '5px')
        .attr('ry', '5px')
        .attr('stroke-linejoin', 'round')
        .attr('fill', 'none');

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

    vis.append('rect')
        .attr('fill', 'none')
        .attr('pointer-events', 'all')
        .attr('width', width - margins.right)
        .attr('height', height)
        .on('mouseover', () => { focus.style('display', null); })
        .on('mouseout', () => { focus.style('display', 'none'); })
        .on('mousemove', mousemove);

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
}