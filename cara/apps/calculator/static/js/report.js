/* Generate the concentration plot using d3 library. */
function draw_concentration_plot(svg_id, times, concentrations, exposed_presence_intervals) {
    
    var time_format = d3.timeFormat('%H:%M');

    // H:M time format for x axis.
    var data = []
    // Prepare data
    times.map((time, index) => data.push({'time': time, 'hour': new Date().setHours(Math.trunc(time), (time - Math.trunc(time)) * 60), 'concentration': concentrations[index] }))

    // Add main SVG element
    var plot_div = document.getElementById(svg_id);
    var vis = d3.select(plot_div).append('svg');
    
    var xRange = d3.scaleTime().domain([data[0].hour, data[data.length - 1].hour]);
    var xTimeRange = d3.scaleLinear().domain([data[0].time, data[data.length - 1].time]);
    var bisecHour = d3.bisector((d) => { return d.hour; }).left;

    var yRange = d3.scaleLinear().domain([0., Math.max(...concentrations)]);

    // Line representing the mean concentration.
    var lineFunc = d3.line();
    var draw_line = vis.append('svg:path')
        .attr('stroke', '#1f77b4')
        .attr('stroke-width', 2)
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

    // Plot tittle.
    var plotTitleEl = vis.append('svg:foreignObject')
        .attr("background-color", "transparent")
        .attr('height', 30)
        .style('text-align', 'center')
        .html('<b>Mean concentration of virions</b>');

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

    // Legend for the plot elements - line and area.
    var legendLineIcon = vis.append('rect')
        .attr('width', 20)
        .attr('height', 3)
        .style('fill', '#1f77b4');

    var legendAreaIcon = vis.append('rect')
        .attr('width', 20)
        .attr('height', 20)
        .attr('fill', '#1f77b4')
        .attr('fill-opacity', '0.1');

    var legendLineText = vis.append('text')
        .text('Mean concentration')
        .style('font-size', '15px')
        .attr('alignment-baseline', 'central');

    var legendAreaText = vis.append('text')
        .text('Presence of exposed person(s)')
        .style('font-size', '15px')
        .attr('alignment-baseline', 'central');

    // Legend bounding
    var legendBBox = vis.append('rect')
        .attr('width', 275)
        .attr('height', 50)
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

    var tooltip_rect = focus.append('rect')
        .attr('fill', 'white')
        .attr('stroke', '#000')
        .attr('width', 80)
        .attr('height', 50)
        .attr('y', -22)
        .attr('rx', 4)
        .attr('ry', 4);

    var tooltip_time = focus.append('text')
        .attr('id', 'tooltip-time')
        .attr('y', -2);

    var tooltip_concentration = focus.append('text')
        .attr('id', 'tooltip-concentration')
        .attr('y', 18);

    var toolBox = vis.append('rect')
        .attr('fill', 'none')
        .attr('pointer-events', 'all')
        .on('mouseover', () => { focus.style('display', null); })
        .on('mouseout', () => { focus.style('display', 'none'); })
        .on('mousemove', mousemove);

    var graph_width;
    var graph_height;

    function redraw() {

        // Define width and height according to the screen size.
        var div_width = plot_div.clientWidth;
        var div_height = plot_div.clientHeight;
        graph_width = div_width;
        graph_height = div_height
        if (div_width >= 900) { // For screens with width > 900px legend can be on the graph's right side.
            var margins = { top: 30, right: 20, bottom: 50, left: 50 };
            div_width = 900;
            graph_width = div_width * (2/3);
            const svg_margins = {'margin-left': '0rem', 'margin-top': '0rem'};
            Object.entries(svg_margins).forEach(([prop,val]) => vis.style(prop,val));
        }
        else {
            var margins = { top: 30, right: 20, bottom: 50, left: 40 };
            div_width = div_width * 1.1
            graph_width = div_width;
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
        yRange.range([graph_height - margins.bottom, margins.top])

        // Line.
        lineFunc.defined(d => !isNaN(d.concentration))
            .x(d => xTimeRange(d.time))
            .y(d => yRange(d.concentration));
        draw_line.attr("d", lineFunc(data));

        // Area.
        exposed_presence_intervals.forEach((b, index) => {
            exposedArea[index].x(d => xTimeRange(d.time))
                .y0(graph_height - margins.bottom)
                .y1(d => yRange(d.concentration));
    
            drawArea[index].attr('d', exposedArea[index](data.filter(d => {
                    return d.time >= b[0] && d.time <= b[1]
            })));
        });

        // Title.
        plotTitleEl.attr('width', graph_width);

        // Axis.
        var xAxis = d3.axisBottom(xRange).tickFormat(d => time_format(d));
        var yAxis = d3.axisLeft(yRange);

        xAxisEl.attr('transform', 'translate(0,' + (graph_height - margins.bottom) + ')')
            .call(xAxis);
        xAxisLabelEl.attr('x', (graph_width + margins.right) / 2)
            .attr('y', graph_height * 0.97);

        yAxisEl.attr('transform', 'translate(' + margins.left + ',0)').call(yAxis);
        yAxisLabelEl.attr('x', (graph_height * 0.9 + margins.bottom) / 2)
            .attr('y', (graph_height + margins.left) * 0.90)
            .attr('transform', 'rotate(-90, 0,' + graph_height + ')');

        // Legend on right side.
        const size = 20;
        if (plot_div.clientWidth >= 900) {
            legendLineIcon.attr('x', graph_width + size)
                .attr('y', margins.top + size);
            legendLineText.attr('x', graph_width + 3 * size)
                .attr('y', margins.top + size);
            legendAreaIcon.attr('x', graph_width + size)
                .attr('y', margins.top + 1.5 * size);
            legendAreaText.attr('x', graph_width + 3 * size)
                .attr('y', margins.top + 2 * size);
            legendBBox.attr('x', graph_width * 1.005)
                .attr('y', margins.top * 1.2);
        }
        // Legend on the bottom.
        else {
            legendLineIcon.attr('x', size * 0.5)
                .attr('y', graph_height * 1.05);
            legendLineText.attr('x', 2 * size)
                .attr('y', graph_height * 1.05);
            legendAreaIcon.attr('x', size * 0.50)
                .attr('y', graph_height * 1.01 + size);
            legendAreaText.attr('x', 2 * size)
                .attr('y', graph_height + 1.7 * size);
            legendBBox.attr('x', 1)
                .attr('y', graph_height * 1.01);
        }
        
        // ToolBox.
        toolBox.attr('width', graph_width - margins.right)
            .attr('height', graph_height);
    }

    // Draw for the first time to initialize.
    redraw();

    function mousemove() {
        if (d3.pointer(event)[0] < graph_width / 2) {
            tooltip_rect.attr('x', 10)
            tooltip_time.attr('x', 18)
            tooltip_concentration.attr('x', 18);
        }
        else {
            tooltip_rect.attr('x', -90)
            tooltip_time.attr('x', -82)
            tooltip_concentration.attr('x', -82)
        }
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

    // Plot title.
    var plotTitleEl = vis.append('svg:foreignObject')
        .attr("background-color", "transparent")
        .attr('height', 30)
        .style('text-align', 'center')
        .html('<b>Mean concentration of virions</b>');
    

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
            var margins = { top: 30, right: 20, bottom: 50, left: 50 };
            div_width = 900;
            graph_width = div_width * (2/3);
            const svg_margins = {'margin-left': '0rem'};
            Object.entries(svg_margins).forEach(([prop,val]) => vis.style(prop,val));
        }
        else {
            var margins = { top: 30, right: 20, bottom: 50, left: 40 };
            div_width = div_width * 1.1
            graph_width = div_width;
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
                label_text[scenario_name].attr('x', margins.left * 1.3)
                    .attr('y', graph_height + size);
            }

        }

        // Title.
        plotTitleEl.attr('width', graph_width);

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
                .attr('y', graph_height * 1.01)
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