import { Routes } from '@angular/router';
import { WindshieldDashboardComponent } from './components/windshield-dashboard/dashboard.component';
import { AppComponent } from './app.component';
import { WindshieldHomeComponent } from './components/windshield-home/home.component';

export const routes: Routes = [
    {
        path: '',
        component: WindshieldHomeComponent,
        data: { title: 'Home' }
    },
    {
        path: 'dashboard',
        component: WindshieldDashboardComponent,
        data: { title: 'Windshield Dashboard' }
    },
    {
        path: '**',
        redirectTo: ''
    }
];
