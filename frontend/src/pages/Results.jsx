import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import toast from 'react-hot-toast';
import { useAuth } from '../contexts/AuthContext';
import { API_BASE_URL } from '../config';
import ResultTable from '../components/ResultTable';
import Timeline from '../components/Timeline';
import {
  ClockIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ArrowLeftIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';

const Results = () => {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();

  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showTimeline, setShowTimeline] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  const maxRetries = 30; // 30 retries * 2 seconds = 1 minute max wait

  useEffect(() => {
    if (jobId) {
      fetchResults();
    }
  }, [jobId]);

  const fetchResults = async () => {
    try {
      setError(null);
      const response = await axios.get(`${API_BASE_URL}/api/result/${jobId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      const data = response.data;

      setJob(data);

      if (data.status === 'processing' && retryCount < maxRetries) {
        // Continue polling for processing jobs
        setTimeout(() => {
          setRetryCount(prev => prev + 1);
          fetchResults();
        }, 2000); // Poll every 2 seconds
      } else if (data.status === 'processing' && retryCount >= maxRetries) {
        setError('Processing is taking longer than expected. Please check back later.');
        setLoading(false);
      } else {
        setLoading(false);
        if (data.status === 'completed') {
          setRetryCount(0);
          toast.success('Document processed successfully!');
        } else if (data.status === 'failed') {
          setError(data.error || 'Processing failed');
        }
      }

    } catch (err) {
      console.error('Error fetching results:', err);
      setError(err.response?.data?.detail || 'Failed to fetch results');
      setLoading(false);
    }
  };

  const handleExport = async (format) => {
    try {
      toast.loading(`Preparing ${format.toUpperCase()} export...`);

      const response = await axios.post(
        `${API_BASE_URL}/api/export/${jobId}?type=${format}`,
        {},
        {
          responseType: 'blob',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `sof_events_${jobId.substring(0, 8)}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      toast.dismiss();
      toast.success(`${format.toUpperCase()} file downloaded successfully!`);

    } catch (err) {
      toast.dismiss();
      console.error('Export failed:', err);
      toast.error(`Export failed: ${err.response?.data?.detail || 'Unknown error'}`);
    }
  };

  const handleRetry = () => {
    setLoading(true);
    setError(null);
    setRetryCount(0);
    fetchResults();
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'processing':
        return <ClockIcon className="h-5 w-5 text-yellow-500 animate-spin" />;
      case 'completed':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <ExclamationCircleIcon className="h-5 w-5 text-red-500" />;
      default:
        return <ClockIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'processing':
        return 'Processing document...';
      case 'completed':
        return 'Processing completed';
      case 'failed':
        return 'Processing failed';
      default:
        return 'Unknown status';
    }
  };

  if (!jobId) {
    return (
      <div className="text-center py-12">
        <ExclamationCircleIcon className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-maritime-navy mb-2">
          Invalid Job ID
        </h2>
        <p className="text-maritime-gray-600 mb-4">
          The job ID is missing or invalid.
        </p>
        <button
          onClick={() => navigate('/')}
          className="btn-primary"
        >
          <ArrowLeftIcon className="h-4 w-4 mr-2" />
          Back to Upload
        </button>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <ExclamationCircleIcon className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-maritime-navy mb-2">
          Error
        </h2>
        <p className="text-maritime-gray-600 mb-6 max-w-md mx-auto">
          {error}
        </p>
        <div className="flex justify-center space-x-4">
          <button
            onClick={handleRetry}
            className="btn-secondary"
          >
            <ArrowPathIcon className="h-4 w-4 mr-2" />
            Retry
          </button>
          <button
            onClick={() => navigate('/')}
            className="btn-primary"
          >
            <ArrowLeftIcon className="h-4 w-4 mr-2" />
            Back to Upload
          </button>
        </div>
      </div>
    );
  }

  if (loading || !job) {
    return (
      <div className="text-center py-12">
        <div className="spinner mx-auto mb-4"></div>
        <h2 className="text-xl font-semibold text-maritime-navy mb-2">
          Loading Results...
        </h2>
        <p className="text-maritime-gray-600">
          Please wait while we fetch your results.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-maritime-navy mb-2">
            Processing Results
          </h1>
          <div className="flex items-center space-x-3">
            {getStatusIcon(job.status)}
            <span className="text-maritime-gray-600">
              {getStatusText(job.status)}
            </span>
          </div>
        </div>

        <button
          onClick={() => navigate('/')}
          className="btn-secondary"
        >
          <ArrowLeftIcon className="h-4 w-4 mr-2" />
          Upload Another
        </button>
      </div>

      {/* Job Information */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <h3 className="font-medium text-maritime-navy mb-1">Document</h3>
            <p className="text-maritime-gray-600 truncate" title={job.filename}>
              {job.filename}
            </p>
          </div>
          <div>
            <h3 className="font-medium text-maritime-navy mb-1">Job ID</h3>
            <p className="text-maritime-gray-600 font-mono text-sm">
              {jobId.substring(0, 8)}...
            </p>
          </div>
          <div>
            <h3 className="font-medium text-maritime-navy mb-1">Status</h3>
            <div className="flex items-center space-x-2">
              {getStatusIcon(job.status)}
              <span className={`
                text-sm font-medium capitalize
                ${job.status === 'completed' ? 'text-green-600' :
                  job.status === 'failed' ? 'text-red-600' : 'text-yellow-600'}
              `}>
                {job.status}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Processing Status */}
      {job.status === 'processing' && (
        <div className="card text-center">
          <div className="animate-pulse-slow">
            <ClockIcon className="h-16 w-16 text-maritime-blue mx-auto mb-4" />
          </div>
          <h3 className="text-lg font-medium text-maritime-navy mb-2">
            Processing Your Document
          </h3>
          <p className="text-maritime-gray-600 mb-4">
            Our AI is analyzing your document and extracting port events.
            This usually takes 15-30 seconds.
          </p>
          <div className="bg-maritime-gray-200 rounded-full h-2 max-w-md mx-auto">
            <div className="bg-maritime-blue h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
          </div>
          <p className="text-sm text-maritime-gray-500 mt-2">
            Attempt {retryCount + 1} of {maxRetries}
          </p>
        </div>
      )}

      {/* Results */}
      {job.status === 'completed' && job.events && (
        <>
          <ResultTable
            events={job.events}
            jobId={jobId}
            onExport={handleExport}
            onViewTimeline={() => setShowTimeline(true)}
          />

          {/* Timeline Modal */}
          {showTimeline && (
            <Timeline
              events={job.events}
              onClose={() => setShowTimeline(false)}
            />
          )}
        </>
      )}

      {/* Failed Status */}
      {job.status === 'failed' && (
        <div className="card text-center">
          <ExclamationCircleIcon className="h-16 w-16 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-maritime-navy mb-2">
            Processing Failed
          </h3>
          <p className="text-maritime-gray-600 mb-4">
            {job.error || 'The document could not be processed. Please try with a different file.'}
          </p>
          <div className="flex justify-center space-x-4">
            <button onClick={handleRetry} className="btn-secondary">
              <ArrowPathIcon className="h-4 w-4 mr-2" />
              Retry Processing
            </button>
            <button onClick={() => navigate('/')} className="btn-primary">
              Upload New Document
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Results;
