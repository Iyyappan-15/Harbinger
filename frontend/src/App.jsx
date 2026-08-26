import React, { useState, useEffect } from 'react';
import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  Box,
  Drawer,
  AppBar,
  Toolbar,
  List,
  Typography,
  Divider,
  IconButton,
  Container,
  Grid,
  Paper,
  Card,
  CardContent,
  Button,
  Slider,
  FormGroup,
  FormControlLabel,
  Checkbox,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Chip,
  Tabs,
  Tab,
  Alert,
  Tooltip as MuiTooltip
} from '@mui/material';
import DbIcon from '@mui/icons-material/Storage';
import PlayIcon from '@mui/icons-material/PlayArrow';
import RefreshIcon from '@mui/icons-material/Refresh';
import HistoryIcon from '@mui/icons-material/History';
import DashboardIcon from '@mui/icons-material/Dashboard';
import HelpIcon from '@mui/icons-material/Help';
import DownloadIcon from '@mui/icons-material/Download';
import CodeIcon from '@mui/icons-material/Code';
import WarningIcon from '@mui/icons-material/Warning';
import MenuIcon from '@mui/icons-material/Menu';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as ChartTooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  ReferenceDot
} from 'recharts';

const API_URL = "http://localhost:8000";

// Define a professional Dark Theme for presentation
const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#4a9eff',
    },
    secondary: {
      main: '#9b59b6',
    },
    background: {
      default: '#0b0f19',
      paper: '#111827',
    },
    error: {
      main: '#f87171',
    },
    warning: {
      main: '#fbbf24',
    },
    success: {
      main: '#34d399',
    },
  },
  typography: {
    fontFamily: '"Inter", "system-ui", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "Helvetica", "Arial", sans-serif',
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          border: '1px solid #1f2937',
          borderRadius: 8,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
  },
});

const drawerWidth = 320;

export default function App() {
  const [activeTab, setActiveTab] = useState(0);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [dbStatus, setDbStatus] = useState(null);
  const [history, setHistory] = useState([]);
  const [currentSweep, setCurrentSweep] = useState(null);
  const [loading, setLoading] = useState(false);

  // Sweep parameters state
  const [threshold, setThreshold] = useState(2.0);
  const [runs, setRuns] = useState(5);
  const [selectedLevels, setSelectedLevels] = useState([5, 10, 15, 20, 25, 50]);

  const allLevels = [5, 10, 15, 20, 25, 30, 40, 50, 75, 100];

  useEffect(() => {
    fetchDbStatus();
    fetchHistory();
  }, []);

  const fetchDbStatus = async () => {
    try {
      const res = await fetch(`${API_URL}/api/status`);
      const data = await res.json();
      setDbStatus(data);
    } catch (err) {
      console.error("Error fetching db status:", err);
    }
  };

  const fetchHistory = async () => {
    try {
      const res = await fetch(`${API_URL}/api/history`);
      const data = await res.json();
      setHistory(data);
      if (data.length > 0 && !currentSweep) {
        loadHistoryDetail(data[0].filename);
      }
    } catch (err) {
      console.error("Error fetching history:", err);
    }
  };

  const loadHistoryDetail = async (filename) => {
    try {
      setLoading(true);
      const res = await fetch(`${API_URL}/api/history/${filename}`);
      const data = await res.json();
      setCurrentSweep(data);
      if (data.results && data.results.length > 0) {
        // Sync parameters
        const sweepLevels = data.results.map(r => r.selectivity_pct);
        setSelectedLevels(sweepLevels);
      }
      setActiveTab(0); // Switch back to the dashboard tab to view the loaded report
    } catch (err) {
      console.error("Error loading history detail:", err);
    } finally {
      setLoading(false);
    }
  };

  const runSweep = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/run-sweep`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          threshold: threshold,
          levels: selectedLevels,
          runs: runs,
          save: true
        })
      });
      const data = await res.json();
      setCurrentSweep(data);
      fetchDbStatus();
      fetchHistory();
      setActiveTab(0); // Switch to dashboard view
    } catch (err) {
      alert("Sweep failed: " + err);
    } finally {
      setLoading(false);
    }
  };

  const handleLevelChange = (level) => {
    if (selectedLevels.includes(level)) {
      setSelectedLevels(selectedLevels.filter(l => l !== level));
    } else {
      setSelectedLevels([...selectedLevels, level].sort((a, b) => a - b));
    }
  };

  const exportData = (format) => {
    if (!currentSweep) return;
    const blob = new Blob(
      [JSON.stringify(currentSweep, null, 2)],
      { type: 'application/json' }
    );
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `harbinger_sweep_${Date.now()}.${format}`;
    link.click();
  };

  const getCleanPlanName = (planStr) => {
    if (!planStr) return "Unknown";
    const firstLine = planStr.split('\n')[0].trim();
    if (firstLine.includes("Hash Join")) return "Hash Join";
    if (firstLine.includes("Merge Join")) return "Merge Join";
    if (firstLine.includes("Nested Loop")) return "Nested Loop";
    if (firstLine.includes("Seq Scan") || firstLine.includes("Sequential Scan")) return "Seq Scan";
    if (firstLine.includes("Index Scan")) return "Index Scan";
    if (firstLine.includes("Bitmap Heap Scan")) return "Bitmap Scan";
    return firstLine.split(' on ')[0];
  };

  // Helper formatting values
  const getRiskColor = (risk) => {
    if (risk === "Critical Risk") return "error";
    if (risk === "High Risk") return "warning";
    if (risk === "Medium Risk") return "info";
    return "success";
  };

  const formatChartData = () => {
    if (!currentSweep || !currentSweep.results) return [];
    return currentSweep.results.map(r => ({
      name: `${r.selectivity_pct}%`,
      selectivity: r.selectivity_pct,
      runtime: parseFloat(r.median_ms.toFixed(3)),
      slowdown: parseFloat(r.slowdown.toFixed(2)),
      isRegressed: r.is_perf_regression,
      isTransitioned: r.is_plan_transition,
    }));
  };

  const chartData = formatChartData();
  const baselineMedian = currentSweep?.baseline_median_ms || 0;
  const thresholdLimit = baselineMedian * (currentSweep?.threshold || threshold);

  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Box sx={{ display: 'flex' }}>
        
        {/* App Bar */}
        <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1, bgcolor: '#111827', borderBottom: '1px solid #1f2937' }} elevation={0}>
          <Toolbar>
            <IconButton
              color="inherit"
              aria-label="open drawer"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              edge="start"
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
            <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1, fontWeight: 'bold', letterSpacing: 0.5 }}>
              HARBINGER <span style={{ fontSize: 13, color: '#888', fontWeight: 'normal' }}>| Query Fragility Analysis Engine</span>
            </Typography>
            
            {/* Live Database status Badge */}
            {dbStatus ? (
              <Chip
                icon={<DbIcon />}
                label={dbStatus.database_connected ? `DB Active (Selectivity: ${dbStatus.selectivity_pct}%)` : "DB Offline"}
                color={dbStatus.database_connected ? "success" : "error"}
                variant="outlined"
                sx={{ mr: 2 }}
              />
            ) : (
              <Chip icon={<DbIcon />} label="Connecting DB..." color="warning" variant="outlined" sx={{ mr: 2 }} />
            )}
            <IconButton onClick={fetchDbStatus} color="inherit" size="small">
              <RefreshIcon />
            </IconButton>
          </Toolbar>
        </AppBar>

        {/* Sidebar Settings Panel */}
        <Drawer
          variant="permanent"
          sx={{
            width: sidebarOpen ? drawerWidth : 0,
            flexShrink: 0,
            transition: 'width 0.2s ease-in-out',
            [`& .MuiDrawer-paper`]: {
              width: drawerWidth,
              boxSizing: 'border-box',
              bgcolor: '#0f1322',
              borderRight: '1px solid #1f2937',
              transform: sidebarOpen ? 'none' : `translateX(-${drawerWidth}px)`,
              transition: 'transform 0.2s ease-in-out',
            },
          }}
        >
          <Toolbar />
          <Box sx={{ p: 3 }}>
            <Typography variant="subtitle2" sx={{ color: '#888', mb: 2, letterSpacing: 1, textTransform: 'uppercase', fontSize: 11 }}>
              Configure Sweep Experiment
            </Typography>

            {/* Threshold Slider */}
            <Box sx={{ mb: 4 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2">Regression Threshold</Typography>
                <Typography variant="body2" color="primary" sx={{ fontWeight: 'bold' }}>{threshold}x</Typography>
              </Box>
              <Slider
                value={threshold}
                onChange={(e, val) => setThreshold(val)}
                min={1.2}
                max={5.0}
                step={0.1}
                valueLabelDisplay="auto"
              />
              <Typography variant="body2" sx={{ color: '#cbd5e1', fontSize: '13px', mt: 0.5, display: 'block', lineHeight: 1.35 }}>
                Cross this limit (x baseline) to trigger Performance Fragility (FT_runtime).
              </Typography>
            </Box>

            {/* Runs slider */}
            <Box sx={{ mb: 4 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2">Warm-Cache Runs</Typography>
                <Typography variant="body2" color="primary" sx={{ fontWeight: 'bold' }}>{runs}</Typography>
              </Box>
              <Slider
                value={runs}
                onChange={(e, val) => setRuns(val)}
                min={3}
                max={10}
                step={1}
                valueLabelDisplay="auto"
              />
              <Typography variant="body2" sx={{ color: '#cbd5e1', fontSize: '13px', mt: 0.5, display: 'block', lineHeight: 1.35 }}>
                Number of executions evaluated to determine the median query runtime.
              </Typography>
            </Box>

            {/* Selectivity checklist */}
            <Box sx={{ mb: 4 }}>
              <Typography variant="body2" sx={{ mb: 1 }}>Selectivity Range (%)</Typography>
              <Paper variant="outlined" sx={{ p: 2, maxHeight: 180, overflowY: 'auto', bgcolor: '#0b0f19' }}>
                <FormGroup>
                  {allLevels.map((lvl) => (
                    <FormControlLabel
                      key={lvl}
                      control={
                        <Checkbox
                          checked={selectedLevels.includes(lvl)}
                          onChange={() => handleLevelChange(lvl)}
                          size="small"
                        />
                      }
                      label={`${lvl}% selectivity`}
                      componentsProps={{ typography: { fontSize: 13 } }}
                    />
                  ))}
                </FormGroup>
              </Paper>
            </Box>

            {/* Run button */}
            <Button
              variant="contained"
              fullWidth
              size="large"
              startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <PlayIcon />}
              onClick={runSweep}
              disabled={loading || selectedLevels.length === 0}
              sx={{ py: 1.5, fontWeight: 'bold' }}
            >
              {loading ? "Sweeping Live DB..." : "Execute Sweep"}
            </Button>
          </Box>
        </Drawer>

        {/* Main Work Area */}
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            p: 3,
            width: sidebarOpen ? `calc(100% - ${drawerWidth}px)` : '100%',
            transition: 'width 0.2s / transform 0.2s ease-in-out',
          }}
        >
          <Toolbar />
          
          {/* Top Tabs */}
          <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
            <Tabs value={activeTab} onChange={(e, val) => setActiveTab(val)}>
              <Tab icon={<DashboardIcon />} iconPosition="start" label="Engine Dashboard" />
              <Tab icon={<HistoryIcon />} iconPosition="start" label="Historical Sweeps" />
              <Tab icon={<CodeIcon />} iconPosition="start" label="Benchmark Details" />
            </Tabs>
          </Box>

          {activeTab === 0 && (
            <Container maxWidth="xl" disableGutters>
              
              {/* Load Loader */}
              {loading && (
                <Alert severity="info" icon={<CircularProgress size={20} />} sx={{ mb: 3 }}>
                  Performing warm execution timings across {selectedLevels.length} selectivity checkpoints. Do not shut down PostgreSQL.
                </Alert>
              )}

              {currentSweep ? (
                <>
                  {/* Summary Metric Cards */}
                  <Grid container spacing={3} sx={{ mb: 3 }}>
                    
                    {/* FT_runtime card */}
                    <Grid item xs={12} sm={6} md={3}>
                      <Card sx={{ borderLeft: `5px solid ${currentSweep.ft_runtime ? '#f87171' : '#1f2937'}` }}>
                        <CardContent>
                          <Typography color="text.secondary" variant="caption" sx={{ textTransform: 'uppercase', letterSpacing: 0.5 }}>
                            Performance Fragility (FT_runtime)
                          </Typography>
                          <Typography variant="h4" sx={{ fontWeight: 'bold', mt: 1 }}>
                            {currentSweep.ft_runtime !== null ? `${currentSweep.ft_runtime}%` : "None"}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            First level experiencing &gt;={currentSweep.threshold || threshold}x slowdown
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>

                    {/* PTT card */}
                    <Grid item xs={12} sm={6} md={3}>
                      <Card sx={{ borderLeft: `5px solid ${currentSweep.ptt ? '#9b59b6' : '#1f2937'}` }}>
                        <CardContent>
                          <Typography color="text.secondary" variant="caption" sx={{ textTransform: 'uppercase', letterSpacing: 0.5 }}>
                            Plan Transition (PTT)
                          </Typography>
                          <Typography variant="h4" sx={{ fontWeight: 'bold', mt: 1, color: '#9b59b6', fontSize: currentSweep.ptt !== null ? 20 : 28 }}>
                            {currentSweep.ptt !== null ? (
                              `${currentSweep.ptt}% (${getCleanPlanName(currentSweep.results.find(r => r.selectivity_pct === currentSweep.ptt)?.plan_structure)})`
                            ) : "None"}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Selectivity where plan type changes
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>

                    {/* Risk Rating card */}
                    <Grid item xs={12} sm={6} md={3}>
                      <Card sx={{ borderLeft: '5px solid transparent' }}>
                        <CardContent>
                          <Typography color="text.secondary" variant="caption" sx={{ textTransform: 'uppercase', letterSpacing: 0.5 }}>
                            Risk Classification
                          </Typography>
                          <Box sx={{ mt: 1 }}>
                            <Chip
                              label={currentSweep.risk_classification || "Low"}
                              color={getRiskColor(currentSweep.risk_classification)}
                              sx={{ fontWeight: 'bold', fontSize: 18, height: 38, px: 1 }}
                            />
                          </Box>
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                            Based on FT_runtime selectivity range
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>

                    {/* Baseline Median card */}
                    <Grid item xs={12} sm={6} md={3}>
                      <Card sx={{ borderLeft: '5px solid #34d399' }}>
                        <CardContent>
                          <Typography color="text.secondary" variant="caption" sx={{ textTransform: 'uppercase', letterSpacing: 0.5 }}>
                            Baseline Median Runtime
                          </Typography>
                          <Typography variant="h4" sx={{ fontWeight: 'bold', mt: 1, color: '#34d399' }}>
                            {currentSweep.baseline_median_ms ? `${currentSweep.baseline_median_ms.toFixed(3)} ms` : "0.0 ms"}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Execution time at baseline (5% selectivity)
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                  </Grid>

                  {/* Insight box */}
                  <Paper variant="outlined" sx={{ p: 2.5, mb: 4, bgcolor: '#0b0f19', border: '1px solid #1f2937' }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1, color: '#4a9eff' }}>
                      ENGINE INTERPRETATION:
                    </Typography>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                      {currentSweep.ft_runtime !== null && currentSweep.ptt !== null ? (
                        currentSweep.ft_runtime < currentSweep.ptt ? (
                          `🔴 Case A Detected: Performance degrades at ${currentSweep.ft_runtime}% selectivity before the plan actually switches at ${currentSweep.ptt}%. FT_runtime (${currentSweep.ft_runtime}%) < PTT (${currentSweep.ptt}%). Real-time monitors will miss this silent regression.`
                        ) : currentSweep.ft_runtime > currentSweep.ptt ? (
                          `🟡 Case C Detected: The planner switches plan at ${currentSweep.ptt}%, but performance degradation is delayed until ${currentSweep.ft_runtime}% selectivity.`
                        ) : (
                          `🟠 Performance regression and plan transition occur simultaneously at ${currentSweep.ft_runtime}%.`
                        )
                      ) : currentSweep.ft_runtime !== null ? (
                        `🔴 Case B Detected: Performance degrades at ${currentSweep.ft_runtime}% selectivity but PostgreSQL Query Planner maintains the same plan structure up to the tested maximum. Same Plan != Same Performance.`
                      ) : (
                        `🟢 Case D Detected: No fragility or regressions observed across the tested selectivity range.`
                      )}
                    </Typography>
                  </Paper>

                  {/* Recharts chart */}
                  <Paper variant="outlined" sx={{ p: 3, mb: 4 }}>
                    <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold' }}>
                      Selectivity vs. Execution Median Runtime
                    </Typography>
                    <Box sx={{ width: '100%', height: 350 }}>
                      <ResponsiveContainer>
                        <LineChart data={chartData} margin={{ top: 20, right: 30, left: 10, bottom: 10 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                          <XAxis dataKey="name" stroke="#6b7280" />
                          <YAxis stroke="#6b7280" label={{ value: 'Median Runtime (ms)', angle: -90, position: 'insideLeft', offset: 0, fill: '#6b7280' }} />
                          <ChartTooltip
                            contentStyle={{ backgroundColor: '#111827', borderColor: '#1f2937' }}
                            labelStyle={{ color: '#fff', fontWeight: 'bold' }}
                          />
                          <Legend />
                          
                          {/* Horizon line for 2x baseline threshold limit */}
                          <ReferenceLine
                            y={thresholdLimit}
                            stroke="#fbbf24"
                            strokeDasharray="5 5"
                            label={{ value: `Threshold Limit (${thresholdLimit.toFixed(2)} ms)`, fill: '#fbbf24', position: 'top' }}
                          />

                          <Line
                            type="monotone"
                            dataKey="runtime"
                            stroke="#4a9eff"
                            name="Median Runtime (ms)"
                            strokeWidth={3}
                            activeDot={{ r: 8 }}
                          />

                          {/* Dots highlighting checkpoints */}
                          {chartData.map((d, index) => {
                            if (d.isTransitioned) {
                              return <ReferenceDot key={index} x={d.name} y={d.runtime} r={6} fill="#9b59b6" stroke="none" />;
                            }
                            if (d.isRegressed) {
                              return <ReferenceDot key={index} x={d.name} y={d.runtime} r={6} fill="#f87171" stroke="none" />;
                            }
                            return null;
                          })}
                        </LineChart>
                      </ResponsiveContainer>
                    </Box>
                    <Box sx={{ display: 'flex', gap: 3, mt: 1, justifyContent: 'center' }}>
                      <Typography variant="caption" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: '50%', backgroundColor: '#4a9eff' }}></span> Normal Query
                      </Typography>
                      <Typography variant="caption" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: '50%', backgroundColor: '#f87171' }}></span> Regressed (FT_runtime)
                      </Typography>
                      <Typography variant="caption" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: '50%', backgroundColor: '#9b59b6' }}></span> Plan Changed (PTT)
                      </Typography>
                    </Box>
                  </Paper>

                  {/* Summary Table */}
                  <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold' }}>
                    Checkpoint Measurements Table
                  </Typography>
                  <TableContainer component={Paper} variant="outlined" sx={{ mb: 4 }}>
                    <Table size="small">
                      <TableHead sx={{ bgcolor: '#0b0f19' }}>
                        <TableRow>
                          <TableCell sx={{ fontWeight: 'bold' }}>Selectivity (%)</TableCell>
                          <TableCell sx={{ fontWeight: 'bold' }}>Median Runtime</TableCell>
                          <TableCell sx={{ fontWeight: 'bold' }}>Slowdown Ratio</TableCell>
                          <TableCell sx={{ fontWeight: 'bold' }}>Query Plan</TableCell>
                          <TableCell sx={{ fontWeight: 'bold' }}>FT_runtime Status</TableCell>
                          <TableCell sx={{ fontWeight: 'bold' }}>PTT Status</TableCell>
                          <TableCell sx={{ fontWeight: 'bold' }}>Action Plan</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {currentSweep.results.map((row) => (
                          <TableRow
                            key={row.selectivity_pct}
                            sx={{
                              bgcolor: row.is_plan_transition
                                ? 'rgba(155, 89, 182, 0.15)'
                                : row.is_perf_regression
                                ? 'rgba(248, 113, 113, 0.1)'
                                : 'inherit'
                            }}
                          >
                            <TableCell sx={{ fontWeight: 'bold' }}>{row.selectivity_pct}%</TableCell>
                            <TableCell>{row.median_ms.toFixed(3)} ms</TableCell>
                            <TableCell>{row.slowdown.toFixed(2)}x</TableCell>
                            <TableCell sx={{ fontFamily: 'monospace', fontWeight: 'bold', color: row.is_plan_transition ? '#9b59b6' : '#4a9eff' }}>
                              {getCleanPlanName(row.plan_structure)}
                            </TableCell>
                            <TableCell>
                              {row.is_perf_regression ? (
                                <Chip size="small" label="Regressed" color="error" variant="outlined" />
                              ) : (
                                <Chip size="small" label="Safe" color="success" variant="outlined" />
                              )}
                            </TableCell>
                            <TableCell>
                              {row.is_plan_transition ? (
                                <Chip size="small" label="Changed" color="secondary" />
                              ) : (
                                <Chip size="small" label="Stable" variant="outlined" />
                              )}
                            </TableCell>
                            <TableCell sx={{ fontStyle: 'italic', color: '#aaa', fontSize: 12 }}>
                              {row.is_plan_transition
                                ? "Plan transition: Sequence Scan forced"
                                : row.is_perf_regression
                                ? "Index scan bloat: suggest buffer tuning"
                                : "No action required"}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>

                  {/* Actions/Download buttons */}
                  <Box sx={{ display: 'flex', gap: 2 }}>
                    <Button variant="outlined" startIcon={<DownloadIcon />} onClick={() => exportData('json')}>
                      Export JSON Result
                    </Button>
                  </Box>
                </>
              ) : (
                <Alert severity="warning">
                  No sweep execution results loaded. Configure the settings panel and click **Execute Sweep**.
                </Alert>
              )}
            </Container>
          )}

          {activeTab === 1 && (
            <Container maxWidth="xl" disableGutters>
              <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold' }}>
                Historical Experiments Log
              </Typography>
              <TableContainer component={Paper} variant="outlined">
                <Table>
                  <TableHead sx={{ bgcolor: '#0b0f19' }}>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 'bold' }}>Timestamp</TableCell>
                      <TableCell sx={{ fontWeight: 'bold' }}>Target Table</TableCell>
                      <TableCell sx={{ fontWeight: 'bold' }}>FT_runtime</TableCell>
                      <TableCell sx={{ fontWeight: 'bold' }}>PTT</TableCell>
                      <TableCell sx={{ fontWeight: 'bold' }}>Risk Level</TableCell>
                      <TableCell sx={{ fontWeight: 'bold' }}>Baseline (ms)</TableCell>
                      <TableCell sx={{ fontWeight: 'bold' }}>Action</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {history.length > 0 ? (
                      history.map((run) => (
                        <TableRow key={run.filename}>
                          <TableCell>{new Date(run.timestamp).toLocaleString()}</TableCell>
                          <TableCell>{run.target_table}</TableCell>
                          <TableCell sx={{ fontWeight: 'bold' }}>{run.ft_runtime !== null ? `${run.ft_runtime}%` : 'None'}</TableCell>
                          <TableCell sx={{ color: '#9b59b6', fontWeight: 'bold' }}>{run.ptt !== null ? `${run.ptt}%` : 'None'}</TableCell>
                          <TableCell>
                            <Chip
                              size="small"
                              label={run.risk_classification}
                              color={getRiskColor(run.risk_classification)}
                              sx={{ fontWeight: 'bold' }}
                            />
                          </TableCell>
                          <TableCell>{run.baseline_median_ms.toFixed(3)} ms</TableCell>
                          <TableCell>
                            <Button size="small" variant="contained" onClick={() => loadHistoryDetail(run.filename)}>
                              Load Report
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))
                    ) : (
                      <TableRow>
                        <TableCell colSpan={7} align="center" sx={{ py: 3 }}>
                          No past executions saved. Run a sweep to create one.
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </Container>
          )}

          {activeTab === 2 && (
            <Container maxWidth="xl" disableGutters>
              <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold' }}>
                Target SQL Query and Schema Configuration
              </Typography>
              <Paper variant="outlined" sx={{ p: 3, bgcolor: '#0b0f19', mb: 3 }}>
                <Typography variant="subtitle2" color="primary" sx={{ mb: 1, fontWeight: 'bold' }}>
                  Target Table
                </Typography>
                <Typography variant="body2" sx={{ mb: 3, fontFamily: 'monospace' }}>
                  {dbStatus?.target_table || "harbinger_lab.orders"} (100,000 Total Rows)
                </Typography>

                <Typography variant="subtitle2" color="primary" sx={{ mb: 1, fontWeight: 'bold' }}>
                  Active SELECT Query
                </Typography>
                <pre style={{ margin: 0, padding: 16, backgroundColor: '#111827', border: '1px solid #1f2937', borderRadius: 4, overflowX: 'auto', fontFamily: '"JetBrains Mono", monospace', fontSize: 13 }}>
{`SELECT
    order_id,
    customer_id,
    order_amount
FROM harbinger_lab.orders
WHERE status = 'pending';`}
                </pre>

                <Typography variant="subtitle2" color="primary" sx={{ mt: 3, mb: 1, fontWeight: 'bold' }}>
                  Active EXPLAIN Query
                </Typography>
                <pre style={{ margin: 0, padding: 16, backgroundColor: '#111827', border: '1px solid #1f2937', borderRadius: 4, overflowX: 'auto', fontFamily: '"JetBrains Mono", monospace', fontSize: 13 }}>
{`EXPLAIN (ANALYZE, BUFFERS, TIMING OFF)
SELECT
    order_id,
    customer_id,
    order_amount
FROM harbinger_lab.orders
WHERE status = 'pending';`}
                </pre>
              </Paper>
            </Container>
          )}

        </Box>
      </Box>
    </ThemeProvider>
  );
}
