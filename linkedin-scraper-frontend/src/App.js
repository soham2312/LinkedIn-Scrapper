import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [companyName, setCompanyName] = useState('');
  const [providedWebsite, setProvidedWebsite] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post('http://127.0.0.1:5000/scrape', {
        company_name: companyName,
        provided_website: providedWebsite,
        email: email,
        password: password,
      });
      console.log(response);
      setResult(response.data);
    } catch (error) {
      console.error('There was an error with the request:', error);
      setResult({ error: 'An error occurred while processing your request.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>LinkedIn Company Scraper</h1>
        <form onSubmit={handleSubmit}>
          <div>
            <label>Company Name:</label>
            <input
              type="text"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              required
            />
          </div>
          <div>
            <label>Provided Website:</label>
            <input
              type="text"
              value={providedWebsite}
              onChange={(e) => setProvidedWebsite(e.target.value)}
              required
            />
          </div>
          <div>
            <label>Email:</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div>
            <label>Password:</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button type="submit">Scrape LinkedIn</button>
        </form>
        {loading && <p>Loading...</p>}
        {result && (
          <div className="result">
            {result.error && <p>Error: {result.error}</p>}
            {result.message && <p>{result.message}</p>}
            {result.name && (
              <>
                <h2>Company Info:</h2>
                <p>Name: {result.name}</p>
                <p>Website: {result.website}</p>
                <p>Industry: {result.industry}</p>
                <p>Company Size: {result.company_size}</p>
                <p>Headquarters: {result.headquarters}</p>
                <p>Founded: {result.founded}</p>
                <p>Specialties: {result.specialties}</p>
                <p>Overview: {result.overview}</p>
              </>
            )}
          </div>
        )}
      </header>
    </div>
  );
}

export default App;
