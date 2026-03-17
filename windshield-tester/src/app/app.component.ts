import { Component, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatDividerModule } from '@angular/material/divider';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatMenuModule } from '@angular/material/menu';
import { ThemeService } from './services/theme.service';
import { TranslateService, Lang } from './services/translate.service';
import { TranslatePipe } from './pipes/translate.pipe';

export type TestPhase = 'standby' | 'detecting' | 'measuring' | 'evaluating' | 'complete';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule, FormsModule, MatInputModule, MatSelectModule,
    MatButtonModule, MatProgressBarModule, MatCardModule, MatIconModule,
    MatDividerModule, MatTooltipModule, MatMenuModule, TranslatePipe
  ],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnDestroy {
  // Services
  constructor(public theme: ThemeService, public translate: TranslateService) { }

  // Config
  models = ['VS20', 'VS30', 'VS40'];
  selectedModel = 'VS20';
  tension = 20.0;
  minIntensity = 0.87;
  maxIntensity = 1.26;
  cycleTime = 30; // seconds

  // State
  testPhase: TestPhase = 'standby';
  isTesting = false;
  progress = 0;
  currentIntensity: number | null = null;
  currentResistance: number | null = null;
  testResult: 'PENDING' | 'OK' | 'ERROR' = 'PENDING';
  windshieldId = 0;

  // Readings tracking
  intensityReadings: number[] = [];
  expectedReadings = 0;
  readingsReceived = 0;

  // Sticker
  printSticker: any = null;

  // Languages
  languages: { code: Lang; label: string; flag: string }[] = [
    { code: 'es', label: 'Español', flag: '🇪🇸' },
    { code: 'en', label: 'English', flag: '🇬🇧' },
    { code: 'fr', label: 'Français', flag: '🇫🇷' },
  ];

  private ws: WebSocket | null = null;

  get currentFlag(): string {
    return this.languages.find(l => l.code === this.translate.currentLang())?.flag ?? '🇪🇸';
  }

  startTest() {
    if (this.isTesting) return;

    this.isTesting = true;
    this.progress = 0;
    this.testResult = 'PENDING';
    this.currentIntensity = null;
    this.currentResistance = null;
    this.printSticker = null;
    this.intensityReadings = [];
    this.readingsReceived = 0;
    this.windshieldId = 0; // Hide the ID until backend returns the new actual test_id
    this.testPhase = 'standby';

    this.connectWebSocket();
  }

  private connectWebSocket() {
    if (this.ws) {
      this.ws.close();
    }

    // Connect to the FastAPI WebSocket endpoint
    this.ws = new WebSocket('ws://localhost:8000/ws/test');

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      // Send the start command with all dynamic parameters from the UI
      this.ws?.send(JSON.stringify({
        action: 'start',
        model: this.selectedModel,
        tension: this.tension,
        min_intensity: this.minIntensity,
        max_intensity: this.maxIntensity,
        cycle_time: this.cycleTime
      }));
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.error) {
        console.error('Server error:', data.error);
        this.testResult = 'ERROR';
        this.testPhase = 'complete';
        this.isTesting = false;
        this.ws?.close();
        return;
      }

      // Update Phase
      if (data.phase) {
        this.testPhase = data.phase as TestPhase;
      }

      // Real-time Measurements Stream
      if (data.reading) {
        this.currentIntensity = data.reading.intensity;
        this.currentResistance = data.reading.resistance;
        this.progress = data.reading.progress;
        this.readingsReceived = data.reading.index;
        this.expectedReadings = data.reading.total;
        this.intensityReadings.push(data.reading.intensity);
      }

      // Evaluation Result
      if (data.result) {
        this.windshieldId = data.result.test_id; // Sync with actual DataBase ID
        this.currentIntensity = data.result.final_intensity;
        this.currentResistance = data.result.final_resistance;
        this.testResult = data.result.status as 'OK' | 'ERROR';

        if (this.testResult === 'OK') {
          this.generateSticker(data.result);
        }

        this.isTesting = false;
        this.ws?.close();
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.testResult = 'ERROR';
      this.testPhase = 'complete';
      this.isTesting = false;
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      if (this.isTesting) {
        // If connection drops unexpectedly while testing
        this.testResult = 'ERROR';
        this.testPhase = 'complete';
        this.isTesting = false;
      }
    };
  }

  private generateSticker(resultData: any) {
    const dateObj = resultData.created_at ? new Date(resultData.created_at) : new Date();
    this.printSticker = {
      id: resultData.test_id,
      model: this.selectedModel,
      intensity: resultData.final_intensity,
      resistance: resultData.final_resistance,
      tension: this.tension,
      date: dateObj.toLocaleDateString(),
      time: dateObj.toLocaleTimeString(),
      status: 'APPROVED'
    };
  }

  resetTest() {
    this.testPhase = 'standby';
    this.testResult = 'PENDING';
    this.progress = 0;
    this.currentIntensity = null;
    this.currentResistance = null;
    this.printSticker = null;
    this.intensityReadings = [];
    this.readingsReceived = 0;
  }

  setLanguage(lang: Lang) {
    this.translate.setLang(lang);
  }

  ngOnDestroy() {
    if (this.ws) {
      this.ws.close();
    }
  }
}
