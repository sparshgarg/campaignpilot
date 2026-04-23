// App.jsx — root
const App = () => {
  return (
    <>
      <Nav />
      <Hero />
      <Ribbon />
      <Bento />
      <AgentShowcase />
      <Workflow />
      <MetricBand />
      <Cta />
      <Footer />
    </>
  );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
