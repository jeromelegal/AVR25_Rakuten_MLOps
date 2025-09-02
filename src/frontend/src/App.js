// frontend/src/App.js
import React from 'react';
import { BrowserRouter as Router, Route, Switch, Redirect } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Layout from './components/Layout';
import HomePage from './pages/HomePage';
import AuthPage from './pages/AuthPage';
import PrivateRoute from './routing/PrivateRoute';
import DataLake from './pages/DataLake';
import DataTransform from './pages/DataTransform';
import DataLoad from './pages/DataLoad';
import DataAnalyse from './pages/DataAnalyse';
import DataLearn from './pages/DataLearn';
import './App.css'; // Importer le fichier CSS global

const App = () => {
  return (
    <AuthProvider>
      <Router>
        <Layout>
          <Switch>
            <PrivateRoute path="/home" component={HomePage} />
            <Route path="/auth" component={AuthPage} />
            <PrivateRoute path="/datalake" component={DataLake} />
            <PrivateRoute path="/datatransform" component={DataTransform} />
            <PrivateRoute path="/dataload" component={DataLoad} />
            <PrivateRoute path="/dataanalyse" component={DataAnalyse} />
            <PrivateRoute path="/datalearn" component={DataLearn} />
            <Redirect from="/" to="/home" />
          </Switch>
        </Layout>
      </Router>
    </AuthProvider>
  );
};

export default App;
