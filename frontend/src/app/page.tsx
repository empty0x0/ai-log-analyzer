export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          AI Log Analyzer
        </h1>

        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Upload Logs</h2>
          <p className="text-gray-600 mb-4">
            Upload Nginx, Apache, or syslog files for AI-powered analysis.
          </p>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
            <p className="text-gray-500">
              Drag and drop a log file here, or click to select
            </p>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Query Logs</h2>
          <p className="text-gray-600 mb-4">
            Ask questions about your logs in natural language.
          </p>
          <input
            type="text"
            placeholder="What errors occurred in the last hour?"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>
    </main>
  );
}
