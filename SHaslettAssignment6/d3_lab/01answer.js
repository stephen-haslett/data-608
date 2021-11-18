d3.csv('ue_industry.csv', data => {
    // Define your scales and generator here.
    const xScale = d3.scaleLinear()
      .domain(d3.extent(data, d => +d.index))
      .range([1180, 20]);

    const yScale = d3.scaleLinear()
      .domain(d3.extent(data, d => +d.Agriculture))
      .range([580, 20]);


	  let line = d3.line()
				.x(d => xScale(+d.index))
				.y(d => yScale(+d['Agriculture']))
				.curve(d3.curveCardinal);

    d3.select('#answer1')
      .append('path')
		  .attr('d', line(data))
		  .attr('stroke', '#DC143C')
});
