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
import NewProduct from './pages/NewProduct';
import FindProduct from './pages/FindProduct';
import SearchAds from './pages/SearchAds';
import AdDetails from './pages/AdDetails';
import './App.css';

const App = () => {
  return (
    <AuthProvider>
      <Router>
        <Layout>
          <Switch>
            {/* Public */}
            <Route exact path="/auth" component={AuthPage} />

            {/* Privées */}
            <PrivateRoute exact path="/home" component={HomePage} />
            <PrivateRoute exact path="/newproduct" component={NewProduct} />
            <PrivateRoute exact path="/findproduct" component={FindProduct} />
            <PrivateRoute exact path="/datalake" component={DataLake} />
            <PrivateRoute exact path="/datatransform" component={DataTransform} />
            <PrivateRoute exact path="/dataload" component={DataLoad} />
            <PrivateRoute exact path="/dataanalyse" component={DataAnalyse} />
            <PrivateRoute exact path="/datalearn" component={DataLearn} />
            <PrivateRoute exact path="/search" component={SearchAds} />
            <PrivateRoute exact path="/ads/:id" component={AdDetails} />

            {/* Redirections */}
            <Redirect exact from="/" to="/home" />

            {/* Catch-all v5 */}
            <Route render={() => <Redirect to="/search" />} />
          </Switch>
        </Layout>
      </Router>
    </AuthProvider>
  );
};

export default App;
