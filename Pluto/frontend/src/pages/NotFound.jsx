import { Link } from 'react-router-dom';

function NotFound() {
  return (
    <div className="container mx-auto px-4 py-8 text-center">
      <h1 className="text-4xl font-bold text-gray-900 mb-4">404 - Page Not Found</h1>
      <p className="text-xl text-gray-600 mb-8">
        The page you're looking for doesn't exist.
      </p>
      <Link to="/" className="btn-primary inline-block">
        Go Home
      </Link>
    </div>
  );
}

export default NotFound;
