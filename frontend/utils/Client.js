import axios from 'axios';

let baseUrl = 'http://127.0.0.1:5000';

const Client = axios.create({
  baseURL: baseUrl,
  headers: {
    'Content-Type': 'application/json',
  },
});

export default Client;