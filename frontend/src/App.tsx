import { Button } from "./components/primitives/button";
import { Card } from "./components/primitives/card";

function App() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="container mx-auto max-w-4xl p-8">
        <h1 className="text-3xl font-bold">FinLab-X</h1>
        <p className="mt-4 text-muted-foreground">AI-powered financial analysis assistant.</p>
      </div>
      <Card>
        <Button className="bg-red-500">Click Me</Button>
      </Card>
    </div>
  );
}

export default App;
