<script>
    import * as d3 from 'd3';
    import { createEventDispatcher } from 'svelte';

    export let stateFeatures;
    export let stateConsumption; // Map: state abbr -> generation MWh
    export let selectedState;
    export let sourceColors;
    export let selectedSource;
    export let stateToName;
    export let colorMax;

    const dispatch = createEventDispatcher();

    let width = 700;
    let height = 440;
    let tooltipText = '';
    let tooltipX = 0;
    let tooltipY = 0;
    let showTooltip = false;
    let legendCanvas;

    let proj = d3.geoAlbersUsa()
        .scale(900)
        .translate([width / 2, height / 2]);
    let path = d3.geoPath().projection(proj);

    $: maxVal = colorMax || 1;

    // Precompute a reactive fill map so Svelte re-renders on data changes
    $: fillMap = (() => {
        const m = new Map();
        for (const f of stateFeatures) {
            const abbr = f.properties.abbr;
            const val = stateConsumption.get(abbr);
            if (!val || val <= 0) {
                m.set(abbr, 'url(#hatch)');
            } else {
                const t = val / maxVal;
                if (selectedSource && sourceColors[selectedSource]) {
                    m.set(abbr, d3.interpolate('#ffffff', sourceColors[selectedSource])(t));
                } else {
                    m.set(abbr, d3.interpolate('#ffffff', '#08519c')(t));
                }
            }
        }
        return m;
    })();

    // Draw legend gradient on canvas
    $: if (legendCanvas && maxVal > 0) {
        const ctx = legendCanvas.getContext('2d');
        const w = 120;
        for (let i = 0; i < w; i++) {
            const t = i / (w - 1);
            if (selectedSource && sourceColors[selectedSource]) {
                ctx.fillStyle = d3.interpolate('#ffffff', sourceColors[selectedSource])(t);
            } else {
                ctx.fillStyle = d3.interpolate('#ffffff', '#08519c')(t);
            }
            ctx.fillRect(i, 0, 1, 12);
        }
    }

    function formatMWh(val) {
        if (!val) return '0';
        if (val >= 1e9) return (val / 1e9).toFixed(1) + 'B';
        if (val >= 1e6) return (val / 1e6).toFixed(1) + 'M';
        if (val >= 1e3) return (val / 1e3).toFixed(0) + 'K';
        return val.toFixed(0);
    }

    function handleClick(abbr) {
        dispatch('selectState', abbr);
    }

    function handleMouseOver(event, abbr) {
        const val = stateConsumption.get(abbr) || 0;
        const name = stateToName[abbr] || abbr;
        tooltipText = `${name}: ${formatMWh(val)} MWh`;
        tooltipX = event.offsetX + 12;
        tooltipY = event.offsetY - 12;
        showTooltip = true;
    }

    function handleMouseOut() {
        showTooltip = false;
    }
</script>

<div class="map-wrapper">
    <svg {width} {height}>
        <defs>
            <pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
                <line x1="0" y1="0" x2="0" y2="6" stroke="#ccc" stroke-width="1.5" />
            </pattern>
        </defs>
        {#each stateFeatures as f}
            {@const abbr = f.properties.abbr}
            {@const d_path = path(f)}
            {#if d_path}
                <path
                    class="state"
                    class:selected={selectedState === abbr}
                    class:dimmed={selectedState && selectedState !== abbr}
                    style="fill: {fillMap.get(abbr) || '#1a1a2e'};"
                    d={d_path}
                    on:click={() => handleClick(abbr)}
                    on:keydown={(e) => { if (e.key === 'Enter') handleClick(abbr); }}
                    on:mouseover={(e) => handleMouseOver(e, abbr)}
                    on:focus={(e) => handleMouseOver(e, abbr)}
                    on:mouseout={handleMouseOut}
                    on:blur={handleMouseOut}
                    role="button"
                    tabindex="0"
                />
            {/if}
        {/each}
    </svg>

    {#if showTooltip}
        <div class="tooltip" style="left: {tooltipX}px; top: {tooltipY}px;">
            {tooltipText}
        </div>
    {/if}

    <div class="legend">
        <span class="legend-label">Low</span>
        <canvas class="legend-canvas" bind:this={legendCanvas} width="120" height="12"></canvas>
        <span class="legend-label">High</span>
        <span class="legend-unit">({formatMWh(maxVal)} MWh max)</span>
    </div>
</div>

<style>
    .map-wrapper {
        position: relative;
    }

    .state {
        stroke: #333;
        stroke-width: 0.5px;
        cursor: pointer;
        transition: opacity 0.15s;
    }

    .state:hover {
        stroke: #fff;
        stroke-width: 1.5px;
    }

    .state.selected {
        stroke: #60a5fa;
        stroke-width: 2.5px;
    }

    .state.dimmed {
        opacity: 0.4;
    }

    .tooltip {
        position: absolute;
        background: rgba(0, 0, 0, 0.9);
        color: #fff;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.85em;
        pointer-events: none;
        white-space: nowrap;
    }

    .legend {
        display: flex;
        align-items: center;
        gap: 4px;
        margin-top: 4px;
        font-size: 0.8em;
    }

    .legend-canvas {
        border-radius: 2px;
    }

    .legend-label {
        opacity: 0.7;
    }

    .legend-unit {
        margin-left: 6px;
        opacity: 0.5;
        font-style: italic;
    }
</style>
