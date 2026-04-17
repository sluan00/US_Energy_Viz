<script>
  import * as d3 from 'd3';
  import { onMount } from 'svelte';
  import * as topojson from 'topojson-client';
  import ChoroplethMap from './ChoroplethMap.svelte';
  import StackedBar from './StackedBar.svelte';
  import LineChart from './LineChart.svelte';
  import TopStatesBar from './TopStatesBar.svelte';

  // Data stores
  let generation = [];      // {year, state, source, generation}
  let fuelPrices = [];       // {year, fuel, price}
  let elecPrices = [];       // {year, state, residential, total}
  let stateFeatures = [];    // GeoJSON features
  let stateNames = {};       // FIPS -> abbreviation

  // Filter state
  let selectedYear = 2024;
  let selectedSource = null; // null = Total
  let selectedState = null;  // null = all states

  const fipsToState = {
    '01':'AL','02':'AK','04':'AZ','05':'AR','06':'CA','08':'CO','09':'CT','10':'DE',
    '11':'DC','12':'FL','13':'GA','15':'HI','16':'ID','17':'IL','18':'IN','19':'IA',
    '20':'KS','21':'KY','22':'LA','23':'ME','24':'MD','25':'MA','26':'MI','27':'MN',
    '28':'MS','29':'MO','30':'MT','31':'NE','32':'NV','33':'NH','34':'NJ','35':'NM',
    '36':'NY','37':'NC','38':'ND','39':'OH','40':'OK','41':'OR','42':'PA','44':'RI',
    '45':'SC','46':'SD','47':'TN','48':'TX','49':'UT','50':'VT','51':'VA','53':'WA',
    '54':'WV','55':'WI','56':'WY'
  };
  const stateToName = {
    'AL':'Alabama','AK':'Alaska','AZ':'Arizona','AR':'Arkansas','CA':'California',
    'CO':'Colorado','CT':'Connecticut','DE':'Delaware','DC':'D.C.','FL':'Florida',
    'GA':'Georgia','HI':'Hawaii','ID':'Idaho','IL':'Illinois','IN':'Indiana',
    'IA':'Iowa','KS':'Kansas','KY':'Kentucky','LA':'Louisiana','ME':'Maine',
    'MD':'Maryland','MA':'Massachusetts','MI':'Michigan','MN':'Minnesota',
    'MS':'Mississippi','MO':'Missouri','MT':'Montana','NE':'Nebraska','NV':'Nevada',
    'NH':'New Hampshire','NJ':'New Jersey','NM':'New Mexico','NY':'New York',
    'NC':'North Carolina','ND':'North Dakota','OH':'Ohio','OK':'Oklahoma',
    'OR':'Oregon','PA':'Pennsylvania','RI':'Rhode Island','SC':'South Carolina',
    'SD':'South Dakota','TN':'Tennessee','TX':'Texas','UT':'Utah','VT':'Vermont',
    'VA':'Virginia','WA':'Washington','WV':'West Virginia','WI':'Wisconsin','WY':'Wyoming'
  };

  const sourceColors = {
    'Coal': '#5c5c5c',
    'Natural Gas': '#e07b39',
    'Nuclear': '#8b5cf6',
    'Hydro': '#3b82f6',
    'Wind': '#22d3ee',
    'Solar': '#facc15',
    'Petroleum': '#a3483b',
  };

  const sources = ['Coal', 'Natural Gas', 'Nuclear', 'Hydro', 'Wind', 'Solar', 'Petroleum'];

  onMount(async function() {
    const [genData, fuelData, elecData, topoData] = await Promise.all([
      d3.csv('generation.csv', d => ({
        year: +d.year,
        state: d.state,
        source: d.source,
        generation: +d.generation
      })),
      d3.csv('fuel-prices.csv', d => ({
        year: +d.year,
        fuel: d.fuel,
        price: +d.price
      })),
      d3.csv('electricity-prices.csv', d => ({
        year: +d.year,
        state: d.state,
        residential: +d.residential,
        total: +d.total
      })),
      d3.json('us-states.json')
    ]);

    generation = genData;
    fuelPrices = fuelData;
    elecPrices = elecData;

    const features = topojson.feature(topoData, topoData.objects.states).features;
    stateFeatures = features.map(f => {
      f.properties.abbr = fipsToState[f.id] || '';
      return f;
    }).filter(f => f.properties.abbr);
  });

  // Global max for color scale: highest total generation any state ever had (across all years)
  $: globalMax = (() => {
    const totals = generation.filter(d => d.source === 'Total');
    return d3.max(totals, d => d.generation) || 1;
  })();

  // Per-source global max: highest generation of each source any state ever had
  $: sourceMax = (() => {
    const map = new Map();
    for (const src of sources) {
      const vals = generation.filter(d => d.source === src);
      map.set(src, d3.max(vals, d => d.generation) || 1);
    }
    return map;
  })();

  $: colorMax = selectedSource ? sourceMax.get(selectedSource) : globalMax;

  // Compute per-state consumption for selected year and source
  $: yearGen = generation.filter(d => d.year === selectedYear);

  $: stateConsumption = (() => {
    const src = selectedSource || 'Total';
    const map = new Map();
    for (const d of yearGen) {
      if (d.source === src) {
        map.set(d.state, d.generation);
      }
    }
    return map;
  })();

  // National average electricity price per year (for line chart)
  $: nationalElecPrice = (() => {
    const byYear = d3.rollups(elecPrices.filter(d => d.total > 0), v => d3.mean(v, d => d.total), d => d.year);
    return byYear.map(([year, price]) => ({year, price})).sort((a,b) => a.year - b.year);
  })();

  // Stacked bar data: energy mix for selected state or national
  $: stackBarData = (() => {
    let filtered = yearGen.filter(d => d.source !== 'Total');
    if (selectedState) {
      filtered = filtered.filter(d => d.state === selectedState);
    }
    const bySource = d3.rollups(filtered, v => d3.sum(v, d => d.generation), d => d.source);
    const total = d3.sum(bySource, d => d[1]);
    const sourceMap = new Map(bySource);
    return sources.map(source => ({
      source,
      generation: sourceMap.get(source) || 0,
      percent: total > 0 ? (sourceMap.get(source) || 0) / total * 100 : 0
    }));
  })();

  // Top 10 states for selected source
  $: topStates = (() => {
    const src = selectedSource || 'Total';
    const filtered = yearGen.filter(d => d.source === src);
    return filtered
      .sort((a, b) => b.generation - a.generation)
      .slice(0, 10)
      .map(d => ({state: d.state, generation: d.generation}));
  })();

  function handleYearChange(event) {
    selectedYear = event.detail;
  }

  function handleSourceSelect(event) {
    const src = event.detail;
    selectedSource = (selectedSource === src) ? null : src;
  }

  function handleStateSelect(event) {
    const st = event.detail;
    selectedState = (selectedState === st) ? null : st;
  }

  $: mapLabel = selectedSource
    ? `${selectedSource} Generation by State (${selectedYear})`
    : `Total Energy Generation by State (${selectedYear})`;

  $: barLabel = selectedState
    ? `Energy Mix: ${stateToName[selectedState] || selectedState} (${selectedYear})`
    : `National Energy Mix (${selectedYear})`;
</script>

<main>
  <h1>U.S. Energy Generation Dashboard</h1>
  <p class="subtitle">Explore shifts in energy sources across states from 1990 to 2024</p>

  <div class="dashboard">
    <div class="top-row">
      <div class="panel map-panel">
        <h2>{mapLabel}</h2>
        <ChoroplethMap
          {stateFeatures}
          {stateConsumption}
          {selectedState}
          {sourceColors}
          {selectedSource}
          {colorMax}
          {stateToName}
          on:selectState={handleStateSelect}
        />
      </div>
      <div class="right-col">
        <div class="panel">
          <h2>{barLabel}</h2>
          <StackedBar
            data={stackBarData}
            {sourceColors}
            {selectedSource}
            on:selectSource={handleSourceSelect}
          />
        </div>
        <div class="panel">
          <h2>Top 10 States: {selectedSource || 'Total'} ({selectedYear})</h2>
          <TopStatesBar
            data={topStates}
            {selectedState}
            {sourceColors}
            {selectedSource}
            on:selectState={handleStateSelect}
          />
        </div>
      </div>
    </div>
    <div class="bottom-row">
      <div class="panel">
        <h2>Fuel Prices & Electricity Cost Over Time</h2>
        <LineChart
          {fuelPrices}
          elecPrices={nationalElecPrice}
          {selectedYear}
          on:yearChange={handleYearChange}
        />
      </div>
    </div>
  </div>
</main>

<style>
  main {
    max-width: 1300px;
    margin: 0 auto;
    padding: 1rem 2rem;
  }

  h1 {
    font-size: 2.2em;
    margin-bottom: 0;
    color: #60a5fa;
  }

  .subtitle {
    margin-top: 0.25rem;
    margin-bottom: 1.5rem;
    font-size: 1.05em;
    opacity: 0.6;
  }

  h2 {
    font-size: 1em;
    margin: 0 0 0.5rem 0;
    color: #93c5fd;
  }

  .dashboard {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .top-row {
    display: flex;
    gap: 1rem;
  }

  .map-panel {
    flex: 1 1 60%;
  }

  .right-col {
    flex: 0 1 40%;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .panel {
    background: #1a1a2e;
    border-radius: 8px;
    padding: 1rem;
  }

  .bottom-row {
    display: flex;
    gap: 1rem;
  }

  .bottom-row .panel {
    flex: 1;
  }
</style>
