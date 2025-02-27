function on_report_load(conditional_probability_viral_loads) {
    // Check/uncheck uncertainties image generation
    document.getElementById('conditional_probability_viral_loads').checked = conditional_probability_viral_loads
}

/* Generate the concentration plot using d3 library. */
function draw_plot(svg_id, group_id, times, concentrations_zoomed, 
                concentrations, cumulative_doses, long_range_cumulative_doses, 
                exposed_presence_intervals, short_range_interactions) {

    // Used for controlling the short-range interactions 
    let button_full_exposure = document.getElementById(`button_full_exposure-group_${group_id}`);
    let button_hide_high_concentration = document.getElementById(`button_hide_high_concentration-group_${group_id}`);
    let long_range_checkbox = document.getElementById(`long_range_cumulative_checkbox-group_${group_id}`);
    let show_sr_legend = short_range_interactions.length > 0;

    let short_range_intervals = short_range_interactions.map((interaction) => interaction["presence_interval"]);
    let short_range_expirations = short_range_interactions.map((interaction) => interaction["expiration"]);

    var data_for_graphs = {
        'concentrations': [],
        'cumulative_doses': [],
        'long_range_cumulative_doses': [],
    }
    times.map((time, index) => data_for_graphs.concentrations.push({ 'time': time, 'hour': new Date().setHours(Math.trunc(time), (time - Math.trunc(time)) * 60), 'concentration': concentrations[index]}));
    times.map((time, index) => data_for_graphs.cumulative_doses.push({ 'time': time, 'hour': new Date().setHours(Math.trunc(time), (time - Math.trunc(time)) * 60), 'concentration': cumulative_doses[index]}));
    times.map((time, index) => data_for_graphs.long_range_cumulative_doses.push({ 'time': time, 'hour': new Date().setHours(Math.trunc(time), (time - Math.trunc(time)) * 60), 'concentration': long_range_cumulative_doses[index]}));

    const tooltip_data_for_graphs = Object.fromEntries(Object.entries(data_for_graphs).filter(([key]) => !key.includes('long_range_cumulative_doses')));

    // Add main SVG element
    var plot_div = document.getElementById(svg_id);
    var vis = d3.select(plot_div).append('svg');

    var time_format = d3.timeFormat('%H:%M');
    // H:M time format for x axis.
    xRange = d3.scaleTime().domain([data_for_graphs.concentrations[0].hour, data_for_graphs.concentrations[data_for_graphs.concentrations.length - 1].hour]),
    xTimeRange = d3.scaleLinear().domain([data_for_graphs.concentrations[0].time, data_for_graphs.concentrations[data_for_graphs.concentrations.length - 1].time]),
    bisecHour = d3.bisector((d) => { return d.hour; }).left,

    yRange = d3.scaleLinear(),
    yCumulativeRange = d3.scaleLinear(),
    
    yAxis = d3.axisLeft(),
    yCumulativeAxis = d3.axisRight();

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
        .text('Mean concentration (IRP/m³)');

    // Y cumulative concentration axis declaration.
    var yAxisCumEl = vis.append('svg:g')
        .attr('class', 'y axis')
        .style("stroke-dasharray", "5 5");

    // Y cumulated concentration axis label.
    var yAxisCumLabelEl = vis.append('svg:text')
        .attr('class', 'y label')
        .attr('fill', 'black')
        .attr('text-anchor', 'middle')
        .text('Mean cumulative dose (IRP)');

    // Legend for the plot elements - line and area.
    
    // Concentration line icon
    var legendLineIcon = vis.append('rect')
        .attr('width', 20)
        .attr('height', 3)
        .style('fill', '#1f77b4');
    // Concentration line text
    var legendLineText = vis.append('text')
        .text('Mean concentration')

    // Cumulative dose line icon
    var legendCumulativeIcon = vis.append('line')
        .style("stroke-dasharray", "5 5") //dashed array for line
        .attr('stroke-width', '2')
        .style("stroke", '#1f77b4');
    // Cumulative dose line text
    var legendCumutiveText = vis.append('text')
        .text('Cumulative dose')

    //  Area line icon
    var legendAreaIcon = vis.append('rect')
        .attr('width', 20)
        .attr('height', 15)
        .attr('fill', '#1f77b4')
        .attr('fill-opacity', '0.1');
    //  Area line text
    var legendAreaText = vis.append('text')
        .text('Presence of exposed person(s)')

    sr_unique_activities = [...new Set(short_range_expirations)]
    if (show_sr_legend) {
        // Long-range cumulative dose line legend - line and area
        var legendLongCumulativeIcon = vis.append('line')
            .style("stroke-dasharray", "5 5") //dashed array for line
            .attr('stroke-width', '2')
            .style("stroke", 'purple')
            .attr('opacity', 0);
        var legendLongCumutiveText = vis.append('text')
            .text('Long-range cumulative dose')
            .attr('opacity', 0);
        // Short-range area icon
        var legendShortRangeAreaIcon = {};
        sr_unique_activities.forEach((b, index) => {
        legendShortRangeAreaIcon[index] = vis.append('rect')
            .attr('width', 20)
            .attr('height', 15);
        // Short-range area icon colors
        if (sr_unique_activities[index] == 'Breathing') legendShortRangeAreaIcon[index].attr('fill', 'red').attr('fill-opacity', '0.2');
        else if (sr_unique_activities[index] == 'Speaking') legendShortRangeAreaIcon[index].attr('fill', 'green').attr('fill-opacity', '0.1');
        else legendShortRangeAreaIcon[index].attr('fill', 'blue').attr('fill-opacity', '0.1');
        });
        // Short-range area text
        var legendShortRangeText = {};
        sr_unique_activities.forEach((b, index) => {
            legendShortRangeText[index] = vis.append('text')
            .text('Short-range - ' + sr_unique_activities[index]);
        });
    }

    // Legend bounding
    if (show_sr_legend) legendBBox_height = 68 + 20 * sr_unique_activities.length;
    else legendBBox_height = 68;
    var legendBBox = vis.append('rect')
        .attr('width', 270)
        .attr('height', legendBBox_height)
        .attr('stroke', 'lightgrey')
        .attr('stroke-width', '2')
        .attr('rx', '5px')
        .attr('ry', '5px')
        .attr('stroke-linejoin', 'round')
        .attr('fill', 'none');

    var clip = vis.append("defs").append("svg:clipPath")
        .attr("id", "clip")
        .append("svg:rect");

    var draw_area = vis.append('svg:g')
        .attr('clip-path', 'url(#clip)');
    // Line representing the mean concentration.
    var lineFunc = d3.line();
    draw_area.append('svg:path')
        .attr('class', 'line')
        .attr('stroke', '#1f77b4')
        .attr('stroke-width', 2)
        .attr('fill', 'none');
    
    // Line representing the cumulative concentration.
    var lineCumulative = d3.line();
    var draw_cumulative_line = draw_area.append('svg:path')
        .attr('stroke', '#1f77b4')
        .attr('stroke-width', 2)
        .style("stroke-dasharray", "5 5")
        .attr('fill', 'none');

    // Line representing the long-range cumulative concentration.
    if (show_sr_legend) {
        var longRangeCumulative = d3.line();
        var draw_long_range_cumulative_line = draw_area.append('svg:path')
            .attr('stroke', 'purple')
            .attr('stroke-width', 2)
            .style("stroke-dasharray", "5 5")
            .attr('fill', 'none')
            .attr('opacity', 0);      
    }

    // Area representing the presence of exposed person(s).
    var exposedArea = {};
    var drawArea = {};
    exposed_presence_intervals.forEach((b, index) => {
        exposedArea[index] = d3.area();
        drawArea[index] = draw_area.append('svg:path')
            .attr('fill', '#1f77b4')
            .attr('fill-opacity', '0.1');
    });

    // Area representing the short-range interaction(s).
    var shortRangeArea = {};
    var drawShortRangeArea = {};
    short_range_intervals?.forEach((b, index) => {
        shortRangeArea[index] = d3.area();
        drawShortRangeArea[index] = draw_area.append('svg:path');

        if (short_range_expirations[index] == 'Breathing') drawShortRangeArea[index].attr('fill', 'red').attr('fill-opacity', '0.2');
        else if (short_range_expirations[index] == 'Speaking') drawShortRangeArea[index].attr('fill', 'green').attr('fill-opacity', '0.1');
        else drawShortRangeArea[index].attr('fill', 'blue').attr('fill-opacity', '0.1');
    });

    // Tooltip.
    var focus = {}, tooltip_rect = {}, tooltip_time = {}, tooltip_concentration = {}, toolBox = {};
    for (const [concentration, data] of Object.entries(tooltip_data_for_graphs)) {
        let data_length = String(Math.floor(Math.max(...data.map(el => el.concentration !== undefined ? el.concentration : 0)))).length;

        focus[concentration] = vis.append('svg:g')
            .style('display', 'none');

        focus[concentration].append('circle')
            .attr('r', 3);

        tooltip_rect[concentration] = focus[concentration].append('rect')
            .attr('fill', 'white')
            .attr('stroke', '#000')
            .attr('width', 65 + data_length * 8)
            .attr('height', 50)
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
            .on('mousemove', mousemove);;
    }

    function update_concentration_plot(concentration_data, cumulative_data) {
        yRange.domain([0., Math.max(...concentration_data)*1.1]);
        yAxisEl.transition().duration(1000).call(yAxis);

        yCumulativeRange.domain([0., Math.max(...cumulative_data)*1.1]);
        yAxisCumEl.transition().duration(1000).call(yCumulativeAxis)
        
        // Concentration line
        lineFunc.defined(d => !isNaN(d.concentration))
            .x(d => xTimeRange(d.time))
            .y(d => yRange(d.concentration));
        draw_area.select('.line')
            .transition()
            .duration(1000)
            .attr("d", lineFunc(data_for_graphs.concentrations));

        // Cumulative line.
        lineCumulative.defined(d => !isNaN(d.concentration))
            .x(d => xTimeRange(d.time))
            .y(d => yCumulativeRange(d.concentration));
        draw_cumulative_line.transition()
            .duration(1000)
            .attr("d", lineCumulative(data_for_graphs.cumulative_doses));
    
        // Long-range cumulative line.
        if (show_sr_legend) {
            longRangeCumulative.defined(d => !isNaN(d.concentration))
                .x(d => xTimeRange(d.time))
                .y(d => yCumulativeRange(d.concentration));
            draw_long_range_cumulative_line.transition()
                .duration(1000)
                .attr("d", lineCumulative(data_for_graphs.long_range_cumulative_doses));
        }

        // Area.
        exposed_presence_intervals.forEach((b, index) => {
            exposedArea[index].x(d => xTimeRange(d.time))
                .y0(graph_height - 50)
                .y1(d => yRange(d.concentration)
            );
            drawArea[index].transition().duration(1000).attr('d', exposedArea[index](data_for_graphs.concentrations.filter(d => {
                    return d.time >= b[0] && d.time <= b[1]
            })));
        });

        // Short-Range Area.
        short_range_intervals.forEach((b, index) => {
            shortRangeArea[index].x(d => xTimeRange(d.time))
                .y0(graph_height - 50)
                .y1(d => yRange(d.concentration));

            drawShortRangeArea[index].transition().duration(1000).attr('d', shortRangeArea[index](data_for_graphs.concentrations.filter(d => {
                return d.time >= b[0] && d.time <= b[1]
            })));
        });

    }

    function redraw() {

        // Define width and height according to the screen size.
        var div_width = plot_div.clientWidth;
        var div_height = plot_div.clientHeight;
        graph_width = div_width;
        graph_height = div_height
        var margins = { top: 30, right: 20, bottom: 50, left: 60 };
        if (div_width >= 1000) { // For screens with width > 1000px legend can be on the graph's right side.
            div_width = 1000;
            graph_width = 600;
            const svg_margins = {'margin-left': '0rem'};
            Object.entries(svg_margins).forEach(([prop,val]) => vis.style(prop,val));
        }
        else {
            div_width = div_width * 1.1
            graph_width = div_width * .9;
            graph_height = div_height * .75; // On mobile screen sizes we want the legend to be on the bottom of the graph.
            const svg_margins = {'margin-left': '-1rem'};
            Object.entries(svg_margins).forEach(([prop,val]) => vis.style(prop,val));
        };

        // Use the extracted size to set the size of the SVG element.
        vis.attr("width", div_width)
            .attr('height', div_height);

        // SVG components according to the width and height.

        // clipPath: everything out of this area won't be drawn.
        clip.attr("x", margins.left)
            .attr("y", margins.top)
            .attr("width", graph_width - margins.right - margins.left)
            .attr("height", graph_height - margins.top - margins.bottom);

        // Axis ranges.
        xRange.range([margins.left, graph_width - margins.right]);
        xTimeRange.range([margins.left, graph_width - margins.right]);
        yRange.range([graph_height - margins.bottom, margins.top]);
        yCumulativeRange.range([graph_height - margins.bottom, margins.top]);

        // Axis.
        var xAxis = d3.axisBottom(xRange).tickFormat(d => time_format(d));
        yAxis.scale(yRange);
        yCumulativeAxis.scale(yCumulativeRange);

        xAxisEl.attr('transform', 'translate(0,' + (graph_height - margins.bottom) + ')')
            .call(xAxis);
        xAxisLabelEl.attr('x', (graph_width + margins.right) / 2)
            .attr('y', graph_height * 0.97);
        
        yAxisEl.attr('transform', 'translate(' + margins.left + ',0)');
        yAxisLabelEl.attr('x', (graph_height + margins.bottom * .55) / 2)
            .attr('y', (graph_height + margins.left) * 0.9)
            .attr('transform', 'rotate(-90, 0,' + graph_height + ')');

        yAxisCumEl.attr('transform', 'translate(' + (graph_width - margins.right) + ',0)').call(yCumulativeAxis);
        yAxisCumLabelEl.attr('transform', 'rotate(-90, 0,' + graph_height + ')')
            .attr('x', (graph_height + margins.bottom) / 2.1);

        if (plot_div.clientWidth >= 1000) {
            yAxisCumLabelEl.attr('y', graph_width * 1.7);
        }
        else {
            yAxisCumLabelEl.attr('y', graph_width + 325);
        }

        const size = 20;
        var legend_x_start = 50;
        const space_between_text_icon = 30;
        const text_height = 6;
        // Legend on right side.
        if (plot_div.clientWidth >= 1000) {
            legendLineIcon.attr('x', graph_width + legend_x_start)
                .attr('y', margins.top + size);
            legendLineText.attr('x', graph_width + legend_x_start + space_between_text_icon)
                .attr('y', margins.top + size + text_height);

            legendCumulativeIcon.attr("x1", graph_width + legend_x_start)
                .attr("x2", graph_width + legend_x_start + 20)
                .attr("y1", margins.top + 2 * size)
                .attr("y2", margins.top + 2 * size);
            legendCumutiveText.attr('x', graph_width + legend_x_start + space_between_text_icon)
                .attr('y', margins.top + 2 * size + text_height);
            
            legendAreaIcon.attr('x', graph_width + legend_x_start)
                .attr('y', margins.top + (3 * size) - 15/2);
            legendAreaText.attr('x', graph_width + legend_x_start + space_between_text_icon)
                .attr('y', margins.top + 3 * size + text_height);
            
            if (show_sr_legend) {
                sr_unique_activities.forEach((b, index) => {
                    legendShortRangeAreaIcon[index].attr('x', graph_width + legend_x_start)
                        .attr('y', margins.top + (4 + index) * size - 15/2);
                    legendShortRangeText[index].attr('x', graph_width + legend_x_start + space_between_text_icon)
                        .attr('y', margins.top + (4 + index) * size + text_height);
                });
                legendLongCumulativeIcon.attr("x1", graph_width + legend_x_start)
                    .attr("x2", graph_width + legend_x_start + 20)
                    .attr("y1", margins.top + (4 + sr_unique_activities.length) * size)
                    .attr("y2", margins.top + (4 + sr_unique_activities.length) * size);
                legendLongCumutiveText.attr('x', graph_width + legend_x_start + space_between_text_icon)
                    .attr('y', margins.top + (4 + sr_unique_activities.length) * size +  + text_height); 
            }
            
            legendBBox.attr('x', graph_width * 1.07)
                .attr('y', margins.top * 1.2);
        }
        // Legend on the bottom.
        else {
            legend_x_start = margins.left + 10;
            legendLineIcon.attr('x', legend_x_start)
                .attr('y', graph_height + size);
            legendLineText.attr('x', legend_x_start + space_between_text_icon)
                .attr('y', graph_height + size + text_height);

            legendCumulativeIcon.attr("x1", legend_x_start)
                .attr("x2", legend_x_start + 20)
                .attr("y1", graph_height + 2 * size)
                .attr("y2", graph_height + 2 * size);
            legendCumutiveText.attr('x', legend_x_start + space_between_text_icon)
                .attr('y', graph_height + 2 * size + text_height);

            legendAreaIcon.attr('x', legend_x_start)
                .attr('y', graph_height + 3 * size - 15/2);
            legendAreaText.attr('x', legend_x_start + space_between_text_icon)
                .attr('y', graph_height + 3 * size + text_height);

            if (show_sr_legend) {
                sr_unique_activities.forEach((b, index) => {
                    legendShortRangeAreaIcon[index].attr('x', legend_x_start)
                        .attr('y', graph_height + (4 + index) * size - 15/2);
                    legendShortRangeText[index].attr('x', legend_x_start + space_between_text_icon)
                        .attr('y', graph_height + (4 + index) * size + text_height);
                });
                legendLongCumulativeIcon.attr("x1", legend_x_start)
                    .attr("x2", legend_x_start + 20)
                    .attr("y1", graph_height + (4 + sr_unique_activities.length) * size)
                    .attr("y2", graph_height + (4 + sr_unique_activities.length) * size)
                legendLongCumutiveText.attr('x', legend_x_start + space_between_text_icon)
                    .attr('y', graph_height + (4 + sr_unique_activities.length) * size + text_height);
            }

            legendBBox.attr('x', margins.left)
                .attr('y', graph_height + 6);
        }

        // ToolBox.
        for (const [concentration, data] of Object.entries(tooltip_data_for_graphs)) {
            toolBox[concentration].attr('width', graph_width - margins.right)
                .attr('height', graph_height);
        }

    }

    if (show_sr_legend) {
        long_range_checkbox.addEventListener("click", () => {
            if (long_range_checkbox.checked) {
                draw_long_range_cumulative_line.transition().duration(1000).attr("opacity", 1);
                legendBBox.transition().duration(1000).attr("height", legendBBox_height + 20);
                legendLongCumulativeIcon.transition().duration(1000).attr("opacity", 1);
                legendLongCumutiveText.transition().duration(1000).attr("opacity", 1);
            }
            else {
                draw_long_range_cumulative_line.transition().duration(1000).attr("opacity", 0);
                legendBBox.transition().duration(1000).attr("height", legendBBox_height);
                legendLongCumulativeIcon.transition().duration(1000).attr("opacity", 0);
                legendLongCumutiveText.transition().duration(1000).attr("opacity", 0);
            }
        });
    };

    if (button_full_exposure) {
        button_full_exposure.addEventListener("click", () => {
            update_concentration_plot(concentrations, cumulative_doses);
            button_full_exposure.disabled = true;
            button_hide_high_concentration.disabled = false;
        });
    }
    if (button_hide_high_concentration) {
        button_hide_high_concentration.addEventListener("click", () => {
            update_concentration_plot(concentrations_zoomed, long_range_cumulative_doses);
            button_full_exposure.disabled = false;
            button_hide_high_concentration.disabled = true;
        });
    }

    function mousemove() {
        for (const [scenario, data] of Object.entries(tooltip_data_for_graphs)) {
            if (d3.pointer(event)[0] < graph_width / 2) {
                tooltip_rect[scenario].attr('x', 10)
                tooltip_time[scenario].attr('x', 18)
                tooltip_concentration[scenario].attr('x', 18);
            }
            else {
                tooltip_rect[scenario].attr('x', -10 - tooltip_rect[scenario].attr('width'))
                tooltip_time[scenario].attr('x', -2 - tooltip_rect[scenario].attr('width'))
                tooltip_concentration[scenario].attr('x', -2 - tooltip_rect[scenario].attr('width'))
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

    // Draw for the first time to initialize.
    redraw(svg_id);
    update_concentration_plot(concentrations, cumulative_doses);

    // Redraw based on the new size whenever the browser window is resized.
    window.addEventListener("resize", e => {
        redraw(svg_id);
        if (button_full_exposure && button_full_exposure.disabled) update_concentration_plot(concentrations, cumulative_doses);
        else update_concentration_plot(concentrations_zoomed, long_range_cumulative_doses)
    });
}

// Generate a scenarios plot using d3 library.
// 'list_of_scenarios' is a dictionary with all the scenarios 
// 'times' is a list of times for all the scenarios
function draw_generic_concentration_plot(
        svg_id,
        times,
        y_axis_label,
        h_lines,
    ) {

    if (svg_id === 'CO2_concentration_graph') {
        list_of_scenarios = {'CO₂ concentration': {'concentrations': CO2_concentrations}};
        min_y_axis_domain = 400;
    }
    else {
        list_of_scenarios = alternative_scenarios;
        min_y_axis_domain = 0;
    }

    // H:M format
    var time_format = d3.timeFormat('%H:%M');
    // D3 array of ten categorical colors represented as RGB hexadecimal strings.
    var colors = d3.schemeCategory10;

    // Variable for the highest concentration for all the scenarios
    var highest_concentration = 0.

    var data_for_scenarios = {}
    for (scenario in list_of_scenarios) {
        scenario_concentrations = list_of_scenarios[scenario].concentrations;

        highest_concentration = Math.max(highest_concentration, Math.max(...scenario_concentrations))

        var data = []
        times.map((time, index) => data.push({ 'time': time, 'hour': new Date().setHours(Math.trunc(time), (time - Math.trunc(time)) * 60), 'concentration': scenario_concentrations[index] }))

        // Add data into lines dictionary
        data_for_scenarios[scenario] = data
    }

    // We need one scenario to get the time range
    var first_scenario = Object.values(data_for_scenarios)[0]

    // Add main SVG element
    var plot_div = document.getElementById(svg_id);
    var vis = d3.select(plot_div).append('svg');

    var xRange = d3.scaleTime().domain([first_scenario[0].hour, first_scenario[first_scenario.length - 1].hour]);
    var xTimeRange = d3.scaleLinear().domain([times[0], times[times.length - 1]]);
    var bisecHour = d3.bisector((d) => { return d.hour; }).left;

    var yRange = d3.scaleLinear();
    var yAxis = d3.axisLeft();

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
        .text(y_axis_label);

    // Legend bounding box.
    let h_lines_lenght = h_lines ? h_lines.length : 0
    let h_line_max_key = h_lines ? Math.max(...(h_lines.map(el => el.label.length))) : 0

    max_key_length = Math.max(Math.max(...(Object.keys(data_for_scenarios).map(el => el.length))), h_line_max_key);
    var legendBBox = vis.append('rect')
        .attr('width', 10 * max_key_length )
        .attr('height', 25 * ((Object.keys(data_for_scenarios).length) + h_lines_lenght))
        .attr('stroke', 'lightgrey')
        .attr('stroke-width', '2')
        .attr('rx', '5px')
        .attr('ry', '5px')
        .attr('stroke-linejoin', 'round')
        .attr('fill', 'none');

    var clip = vis.append("defs").append("svg:clipPath")
        .attr("id", "clip")
        .append("svg:rect");

    var draw_area = vis.append('svg:g')
        .attr('clip-path', 'url(#clip)');

    // Line representing the mean concentration for each scenario.
    var lineFuncs = {}, draw_lines  = {}, label_icons = {}, label_text = {};
    for (const [scenario_name, data] of Object.entries(data_for_scenarios)) {
        var scenario_index = Object.keys(data_for_scenarios).indexOf(scenario_name)

        // Line representing the mean concentration.
        lineFuncs[scenario_name] = d3.line();

        draw_lines[scenario_name] = draw_area.append('svg:path')
            .attr("stroke", colors[scenario_index])
            .attr('stroke-width', 2)
            .attr('fill', 'none');

        // Legend for the plot elements - lines.
        label_icons[scenario_name] = vis.append('rect')
            .attr('width', 20)
            .attr('height', 3)
            .style('fill', colors[scenario_index]);

        label_text[scenario_name] = vis.append('text')
            .text(scenario_name);
    }
    if (h_lines) {
        var h_lines_draw = {}, h_line_label_icon = {}, h_line_label_text = {};
        h_lines.map((line) => {
            h_lines_draw[line.label] = draw_area.append('svg:line')
                .attr('stroke', line.color)
                .attr('stroke-width', 2)
                .attr('stroke-dasharray', line.style == 'dashed' ? (5, 5) : 0)

            // Legend for each of the horizontal lines

            h_line_label_icon[line.label] = vis.append('line')
                .style("stroke-dasharray", line.style == 'dashed' ? (5, 5) : 0)
                .attr('stroke-width', '2')
                .style("stroke", line.color);
            h_line_label_text[line.label] = vis.append('text')
                .text(line.label);
        })
    }

    // Tooltip.
    var focus = {}, tooltip_rect = {}, tooltip_time = {}, tooltip_concentration = {}, toolBox = {};
    for (const [scenario_name, data] of Object.entries(data_for_scenarios)) {
        let data_length = String(Math.floor(Math.max(...data.map(el => el.concentration !== undefined ? el.concentration : 0)))).length;
        focus[scenario_name] = vis.append('svg:g')
            .style('display', 'none');

        focus[scenario_name].append('circle')
            .attr('r', 3);

        tooltip_rect[scenario_name] = focus[scenario_name].append('rect')
            .attr('fill', 'white')
            .attr('stroke', '#000')
            .attr('width', 65 + data_length * 8)
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

    function update_concentration_plot(concentration_data) {
        list_of_scenarios = (svg_id === 'CO2_concentration_graph') ? {'CO₂ concentration': {'concentrations': CO2_concentrations}} : alternative_scenarios
        var highest_concentration = 0.

        for (scenario in list_of_scenarios) {
            scenario_concentrations = list_of_scenarios[scenario][concentration_data];
            highest_concentration = Math.max(highest_concentration, Math.max(...scenario_concentrations));
        }

        yRange.domain([min_y_axis_domain, highest_concentration*1.1]);
        yAxisEl.transition().duration(1000).call(yAxis);

        for (const [scenario_name, data] of Object.entries(data_for_scenarios)) {
            // Lines.
            lineFuncs[scenario_name].defined(d => !isNaN(d.concentration))
                .x(d => xTimeRange(d.time))
                .y(d => yRange(d.concentration));
            draw_lines[scenario_name].transition().duration(1000).attr("d", lineFuncs[scenario_name](data));
        }

        if (h_lines) {
            h_lines.map((line) => {
                h_lines_draw[line.label]
                    .attr("x1", xTimeRange(times[0])) 
                    .attr("y1", yRange(line.y))
                    .attr("x2", xTimeRange(times[times.length - 1]))
                    .attr("y2", yRange(line.y));
            })
        }
    }

    var graph_width;
    var graph_height;

    function redraw(svg_id) {
        // Define width and height according to the screen size. Always use an already defined
        var window_width = document.getElementById(svg_id).clientWidth;
        var div_width = window_width;
        var div_height = document.getElementById(svg_id).clientHeight;
        graph_width = div_width;
        graph_height = div_height;
        var margins = { top: 30, right: 20, bottom: 50, left: 60 };
        if (window_width >= 1000) { // For screens with width > 1000px legend can be on the graph's right side.
            div_width = 1000;
            graph_width = 600;
            const svg_margins = {'margin-left': '0rem'};
            Object.entries(svg_margins).forEach(([prop,val]) => vis.style(prop,val));
        }
        else {
            div_width = div_width * 1.1
            graph_width = div_width * .9;
            graph_height = div_height * .75; // On mobile screen sizes we want the legend to be on the bottom of the graph.
            const svg_margins = {'margin-left': '-1rem'};
            Object.entries(svg_margins).forEach(([prop,val]) => vis.style(prop,val));
        };

        // Use the extracted size to set the size of the SVG element.
        vis.attr("width", div_width)
            .attr('height', div_height);

        // SVG components according to the width and height.
        // clipPath: everything out of this area won't be drawn.
        clip.attr("x", margins.left)
            .attr("y", margins.top)
            .attr("width", graph_width - margins.right - margins.left)
            .attr("height", graph_height - margins.top - margins.bottom);

        // Axis ranges.
        xRange.range([margins.left, graph_width - margins.right]);
        xTimeRange.range([margins.left, graph_width - margins.right]);
        yRange.range([graph_height - margins.bottom, margins.top]);

        // Axis.
        var xAxis = d3.axisBottom(xRange).tickFormat(d => time_format(d));
        yAxis.scale(yRange);

        xAxisEl.attr('transform', 'translate(0,' + (graph_height - margins.bottom) + ')')
            .call(xAxis);
        xAxisLabelEl.attr('x', (graph_width + margins.right) / 2)
            .attr('y', graph_height * 0.97)

        yAxisEl.attr('transform', 'translate(' + margins.left + ',0)')
            .call(yAxis);
        yAxisLabelEl.attr('x', (graph_height + margins.bottom * .55) / 2)
            .attr('y', (graph_height + margins.left) * 0.9)
            .attr('transform', 'rotate(-90, 0,' + graph_height + ')');

        // Legend items
        var legend_x_start = 25;
        const space_between_text_icon = 30;
        const text_height = 6;
        for (const [scenario_name, data] of Object.entries(data_for_scenarios)) {
            var scenario_index = Object.keys(data_for_scenarios).indexOf(scenario_name)
            // Legend on right side.
            var size = 20 * (scenario_index + 1);
            if (window_width >= 1000) {
                label_icons[scenario_name].attr('x', graph_width + legend_x_start)
                    .attr('y', margins.top + size);
                label_text[scenario_name].attr('x', graph_width + legend_x_start + space_between_text_icon)
                    .attr('y', margins.top + size  + text_height);
            }
            // Legend on the bottom.
            else {
                legend_x_start = margins.left + 10;
                label_icons[scenario_name].attr('x', legend_x_start)
                    .attr('y', graph_height + size);
                label_text[scenario_name].attr('x', legend_x_start + space_between_text_icon)
                    .attr('y', graph_height + size  + text_height);
            }
        }
        if (h_lines) {
            h_lines.map((line, index) => {
                size = 21 * (scenario_index + index + 2); // account for previous legend elements
                if (window_width >= 1000) {
                    h_line_label_icon[line.label].attr("x1", graph_width + legend_x_start)
                        .attr("x2", graph_width + legend_x_start + 20)
                        .attr("y1", margins.top + size)
                        .attr("y2", margins.top + size);
                    h_line_label_text[line.label].attr('x', graph_width + legend_x_start + space_between_text_icon)
                        .attr('y', margins.top + size  + text_height);
                }
                // Legend on the bottom.
                else {
                    legend_x_start = margins.left + 10;
                    h_line_label_icon[line.label].attr("x1", legend_x_start)
                        .attr("x2", legend_x_start + 20)
                        .attr("y1", graph_height + size)
                        .attr("y2", graph_height + size);
                    h_line_label_text[line.label].attr('x', legend_x_start + space_between_text_icon)
                        .attr('y', graph_height + size  + text_height);
                }
            })
        }

        // Legend on right side.
        if (window_width >= 1000) {
            legendBBox.attr('x', graph_width * 1.02)
                .attr('y', margins.top * 1.15);
            
        }
        // Legend on the bottom.
        else {
            legendBBox.attr('x', margins.left)
                .attr('y', graph_height * 1.02)
        }

        // ToolBox.
        for (const [scenario_name, data] of Object.entries(data_for_scenarios)) {
            toolBox[scenario_name].attr('width', graph_width - margins.right)
                .attr('height', graph_height);
        }
    }

    function mousemove() {
        for (const [scenario_name, data] of Object.entries(data_for_scenarios)) {
            if (d3.pointer(event)[0] < graph_width / 2) {
                tooltip_rect[scenario_name].attr('x', 10)
                tooltip_time[scenario_name].attr('x', 18)
                tooltip_concentration[scenario_name].attr('x', 18);
            }
            else {
                tooltip_rect[scenario_name].attr('x', -10 - tooltip_rect[scenario_name].attr('width'))
                tooltip_time[scenario_name].attr('x', - tooltip_rect[scenario_name].attr('width'))
                tooltip_concentration[scenario_name].attr('x', - tooltip_rect[scenario_name].attr('width'))
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

    // Draw for the first time to initialize.
    redraw(svg_id);
    update_concentration_plot('concentrations');

    // Redraw based on the new size whenever the browser window is resized.
    window.addEventListener("resize", e => {
        redraw(svg_id);
        update_concentration_plot('concentrations');
    });
}

function draw_histogram(svg_id, prob, prob_sd) {
    // Add main SVG element
    var plot_div = document.getElementById(svg_id);
    var vis = d3.select(plot_div).append('svg');

    let hist_count = prob_hist_count;
    let hist_bins = prob_hist_bins;

    // X axis:
    var xRange = d3.scaleLinear()
        .domain([0, d3.max(hist_bins)]);
    var xEl = vis.append("svg:g")
    
    // X axis label.
    var xLabel = vis.append('text')
        .attr('class', 'x label')
        .attr('fill', 'black')
        .attr('text-anchor', 'middle')
        .text('Probability of Infection');

    // set the parameters for the histogram
    var histogram = d3.histogram()
        .value(d => d)
        .domain(xRange.domain())  // then the domain of the graphic
        .thresholds(xRange.ticks(100)); // then the numbers of bins
    
    // And apply this function to data to get the bins  
    var bins = histogram(prob_dist);

    // Y left axis: scale and draw:
    var yRangeLeft = d3.scaleLinear().domain([0, d3.max(hist_count)]);   // d3.hist has to be called before the Y axis obviously
    var yElLeft = vis.append("svg:g").attr('class', 'y axis');

    // Y left axis label.
    var yLabelLeft = vis.append('svg:text')
        .attr('class', 'y label')
        .attr('fill', 'black')
        .attr('text-anchor', 'middle')
        .text('Density');

    // append the bar rectangles to the svg element
    var histRect = vis.selectAll("rect")
        .data(bins.slice(0, -1))
        .enter()
        .append("rect")
            .attr("x", 1)
            .attr('fill', '#1f77b4');
            
    // Y right axis: scale and draw:
    var yRangeRight = d3.scaleLinear().domain([0, 1]);
    var yElRight = vis.append("svg:g").attr('class', 'y axis');

    // Y right axis label.
    var yLabelRight = vis.append('svg:text')
        .attr('class', 'y label')
        .attr('fill', 'black')
        .attr('text-anchor', 'middle')
        .text('Cumulative Density Function (CDF)');
    
    // CDF Calculation
    let count_sum = hist_count.reduce((partialSum, a) => partialSum + a, 0);
    let pdf = hist_count.map((el, i) => el/count_sum);
    let cdf = pdf.map((sum => value => sum += value)(0));
    // Add the CDF line
    var cdfLine = vis.append("svg:path")
        .datum(cdf)
        .attr("fill", "none")
        .attr("stroke", "lightblue")
        .attr("stroke-width", 1.5);

    // Add the mean dashed line
    var meanLine = vis.append("svg:line")
        .attr("fill", "none")
        .attr('stroke-width', 2)
        .attr('stroke-dasharray', (5, 5))
        .attr("stroke", "grey");

    // Plot tile
    var plotTitle = vis.append("svg:text")
        .attr("text-anchor", "middle")  
        .text(`P(I) -- Mean(SD) = ${prob.toFixed(2)}(${prob_sd.toFixed(2)}) `);

    // CDF line icon
    var cdfLineIcon = vis.append('rect')
        .attr('width', 20)
        .attr('height', 3)
        .style('fill', 'lightblue')
    // CDF line text
    var cdfLineText = vis.append('text').text('CDF')      
    //  Hist icon
    var histIcon = vis.append('rect')
        .attr('width', 20)
        .attr('height', 15)
        .attr('fill', '#1f77b4');
    //  Hist text
    var histText = vis.append('text').text('Histogram');
    // Mean text
    var meanText = vis.append('line')
        .attr('stroke', 'grey')
        .attr('stroke-width', 2)
        .attr('stroke-dasharray', (5, 5));
    var meanLineText = vis.append('text').text('Mean');      

    // Legend Bbox
    var legendBBox = vis.append('rect')
        .attr('width', 120)
        .attr('height', 65)
        .attr('stroke', 'lightgrey')
        .attr('stroke-width', '2')
        .attr('rx', '5px')
        .attr('ry', '5px')
        .attr('stroke-linejoin', 'round')
        .attr('fill', 'none');

    function redraw() {
        // Define width and height according to the screen size.
        var div_width = plot_div.clientWidth;
        var div_height = plot_div.clientHeight;
        graph_width = div_width;
        graph_height = div_height
        var margins = { top: 30, right: 20, bottom: 50, left: 60 };
        if (div_width >= 1000) { // For screens with width > 1000px legend can be on the graph's right side.
            div_width = 1000;
            graph_width = 600;
            const svg_margins = {'margin-left': '0rem'};
            Object.entries(svg_margins).forEach(([prop,val]) => vis.style(prop,val));
        }
        else {
            div_width = div_width * 1.1
            graph_width = div_width * .9;
            graph_height = div_height * .75; // On mobile screen sizes we want the legend to be on the bottom of the graph.
            const svg_margins = {'margin-left': '-1rem'};
            Object.entries(svg_margins).forEach(([prop,val]) => vis.style(prop,val));
        };

        // Use the extracted size to set the size of the SVG element.
        vis.attr("width", div_width)
            .attr('height', div_height);

        // Axis definitions
        xRange.range([margins.left, graph_width - margins.right]);
        xEl.attr("transform", "translate(0," + (graph_height - margins.bottom) + ")").call(d3.axisBottom(xRange));
        xLabel.attr('x', (graph_width + margins.right) / 2).attr('y', graph_height * 0.97);
        
        yRangeLeft.range([graph_height - margins.bottom, margins.top]);
        yElLeft.attr('transform', 'translate(' + margins.left + ',0)').call(d3.axisLeft(yRangeLeft));
        yLabelLeft.attr('x', (graph_height * 0.9 + margins.bottom) / 2)
            .attr('y', (graph_height + margins.left) * 0.9)
            .attr('transform', 'rotate(-90, 0,' + graph_height + ')');
        
        yRangeRight.range([graph_height - margins.bottom, margins.top]);
        yElRight.attr('transform', 'translate(' + (graph_width - margins.right) + ',0)').call(d3.axisRight(yRangeRight));
        yLabelRight.attr('transform', 'rotate(-90, 0,' + graph_height + ')')
            .attr('x', (graph_height + margins.bottom) / 2.1);
        
        if (plot_div.clientWidth >= 1000) yLabelRight.attr('y', graph_width * 1.7);
        else yLabelRight.attr('y', graph_width + 325);

        // Histogram rectangles
        histRect.each(function (d, i) {
            var currentRect = d3.select(this);
            var x0 = xRange(d.x0);
            var x1 = xRange(d.x1);
            var yValue = yRangeLeft(hist_count[i]);
            currentRect
                .attr("transform", "translate(" + x0 + "," + yValue + ")")
                .attr("width", x1 - x0 - 1)
                .attr("height", graph_height - yValue - margins.bottom);
        });

        // CDF line
        cdfLine.attr("d", d3.line()
            .x(function(d, i) { return xRange(hist_bins[i]); })
            .y(function(d) { return yRangeRight(d); }
        ));

        // Mean dashed line
        meanLine.attr("x1", xRange(prob/100))
            .attr("y1", yRangeRight(1))
            .attr("x2", xRange(prob/100))
            .attr("y2", yRangeRight(0));

        // Plot title
        plotTitle.attr("x", xRange(0.5))
            .attr("y", 0 + margins.top);
        
        // Legend for the plot elements
        const size = 15;
        var legend_x_start = 50;
        const space_between_text_icon = 30;
        const text_height = 6;
        if (plot_div.clientWidth >= 1000) {
            // CDF line icon
            cdfLineIcon.attr('x', graph_width + legend_x_start)
                .attr('y', margins.top + size);
            // CDF line text
            cdfLineText.attr('x', graph_width + legend_x_start + space_between_text_icon)
                .attr('y', margins.top + size + text_height);
            // Hist icon
            histIcon.attr('x', graph_width + legend_x_start)
                .attr('y', margins.top + (2 * size));
            // Hist text
            histText.attr('x', graph_width + legend_x_start + space_between_text_icon)
                .attr('y', margins.top + 2 * size + text_height*2);
            // Mean text
            meanText.attr("x1", graph_width + legend_x_start)
                .attr("x2", graph_width + legend_x_start + 20)
                .attr("y1", margins.top + 3.85 * size)
                .attr("y2", margins.top + 3.85 * size);
            // Mean line text
            meanLineText.attr('x', graph_width + legend_x_start + space_between_text_icon)
                .attr('y', margins.top + 3 * size + text_height*3);
            // Legend BBox
            legendBBox.attr('x', graph_width * 1.07)
                .attr('y', margins.top * 1.1);
        }
        else {
            legend_x_start = margins.left + 10;
            // CDF line icon
            cdfLineIcon.attr('x', legend_x_start)
                .attr('y', graph_height + size);
            // CDF line text
            cdfLineText.attr('x', legend_x_start + space_between_text_icon)
                .attr('y', graph_height + size + text_height);
            // Hist icon
            histIcon.attr('x', legend_x_start)
                .attr('y', graph_height + (2 * size));
            // Hist text
            histText.attr('x', legend_x_start + space_between_text_icon)
                .attr('y', graph_height + 2 * size + text_height*2);
            // Mean text
            meanText.attr("x1", legend_x_start)
                .attr("x2", legend_x_start + 20)
                .attr("y1", graph_height + 3.85 * size)
                .attr("y2", graph_height + 3.85 * size);
            // Mean line text
            meanLineText.attr('x', legend_x_start + space_between_text_icon)
                .attr('y', graph_height + 3 * size + text_height*3);
            // Legend BBox
            legendBBox.attr('x', margins.left)
                .attr('y', graph_height + 4);
        }
    }

    // Draw for the first time to initialize.
    redraw();

    // Redraw based on the new size whenever the browser window is resized.
    window.addEventListener("resize", e => {
        redraw();
    });
}

function copy_clipboard(shareable_link) {

    $("#mobile_link").attr('title', 'Copied!')
          .tooltip('_fixTitle')
          .tooltip('show');
          
    navigator.clipboard.writeText(shareable_link);
}

function check_download_button() {
    // Handle the disable property of the download button
    let download_button = document.getElementById('downloadCSV');
    document.querySelectorAll('input[type="checkbox"]:checked').length <= 1 ? download_button.disabled = true : download_button.disabled = false;
}

function display_column_name_warning(checked) {
    let warning_element = document.getElementById("alternative_scenario_warning");
    checked ? warning_element.style.display = 'flex' : warning_element.style.display = 'none';
}

function display_rename_column(bool, id) {
    check_download_button();
    // Change the visibility of renaming section
    if (bool) document.getElementById(id).style.display = 'flex';
    else document.getElementById(id).style.display = 'none';
}

function conditional_probability_viral_loads(value, is_generated) {
    // If the image was previously generated, there is no need to reload the page.
    if (value && is_generated == 1) {
        document.getElementById('conditional_probability_div').style.display = 'block'
    }
    else if (value && is_generated == 0) {
        document.getElementById('label_conditional_probability_viral_loads').innerHTML = `<span id="loading_spinner" class="spinner-border spinner-border-sm mr-2 mt-0" role="status" aria-hidden="true"></span>Loading...`;
        document.getElementById('conditional_probability_viral_loads').setAttribute('disabled', true);
        document.cookie = `conditional_plot= 1; path=/`;
        window.location.reload();
    }
    else document.getElementById('conditional_probability_div').style.display = "none";
}

function export_csv() {
    // This function generates a CSV file according to the user's input.
    // It is composed of a list of lists. 
    // The first item of the main list corresponds to the columns' name.
    // The remaining items correspond to each of the file row, i.e. the 
    // respective data from the selected inputs.

    let final_export = [];
    // Verify which items are checked
    let export_lists = document.getElementsByName('checkedItems');
    let checked_items = []; // The column to be added, with the id to be identified.
    let checked_names = []; // The column with the respective rename.
    let has_alternative_scenario = false;
    export_lists.forEach(e => {
        if (e.checked) {
            if (e.id == "Alternative Scenarios") {
                Object.entries(alternative_scenarios).map((scenario) => {
                    if (scenario[0] != 'Current scenario') {
                        checked_names.push(`Alternative scenario concentration - ${scenario[0]} \u2028(virions m⁻³)`);
                        has_alternative_scenario = true;
                    };
                });
            }
            else if (e.id == "Cumulative Dose") {
                var has_rename = document.getElementById(`${e.id}__rename`).value;
                var column_name = has_rename != '' ? has_rename : e.id;
                if (short_range_expirations.length > 0) {
                    checked_names.push(`Long-Range ${column_name} \u2028(infectious virus)`);
                    checked_items.push('Long-Range Dose');
                    // When we have short range interactions, we want the column for the cumulative dose to have the "Total" word before the column name
                    checked_names.push(`Total ${column_name} \u2028(infectious virus)`); 
                }
                else {
                    checked_names.push(`${column_name} \u2028(infectious virus)`);
                }
                checked_items.push(e.id);
            }
            else {
                var has_rename = document.getElementById(`${e.id}__rename`).value;
                var column_name = has_rename != '' ? has_rename : e.id;
                if (e.id == "Time") checked_names.push(`${column_name} \u2028(h)`);
                else if (e.id == "Concentration") checked_names.push(`${column_name} \u2028(virions m⁻³)`);
                else if (e.id == "CO2_Concentration") checked_names.push(`${column_name} \u2028(ppm)`);
                checked_items.push(e.id);
            }
        }
    });
    final_export.push(checked_names);

    // Add data for each column.
    times.forEach((e, i) => {
        let this_row = [];
        checked_items.includes("Time") && this_row.push(times[i].toFixed(2));
        checked_items.includes("Concentration") && this_row.push(concentrations[i]);
        checked_items.includes("Cumulative Dose") && this_row.push(cumulative_doses[i]);
        checked_items.includes("Long-Range Dose") && this_row.push(long_range_cumulative_doses[i]);
        checked_items.includes("CO2_Concentration") && this_row.push(CO2_concentrations[Object.keys(CO2_concentrations)[0]].concentrations[i]);
        if (has_alternative_scenario) {
            Object.entries(alternative_scenarios).map((scenario) => {
                if (scenario[0] != 'Current scenario') {
                    this_row.push(scenario[1].concentrations[i]);
                };
            });
        };
        final_export.push(this_row);
    });

    // Prepare the CSV file.
    let csvContent = "data:text/csv;charset=utf8," 
        + final_export.map(e => e.join(",")).join("\n");
    var encodedUri = encodeURI(csvContent);
    // Set a name for the file.
    var link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "report_data.csv");
    document.body.appendChild(link);
    link.click();    
}
