import { Component } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { NavigationComponent } from './navigation.component';

@Component({
  standalone: true,
  template: ''
})
class NavigationTestPageComponent {}

describe('NavigationComponent', () => {
  let fixture: ComponentFixture<NavigationComponent>;
  let router: Router;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NavigationComponent],
      providers: [
        provideRouter([
          { path: 'upload', component: NavigationTestPageComponent },
          { path: 'dashboard', component: NavigationTestPageComponent },
          { path: 'transactions', component: NavigationTestPageComponent },
          { path: 'ai-insights', component: NavigationTestPageComponent }
        ])
      ]
    }).compileComponents();

    router = TestBed.inject(Router);
    fixture = TestBed.createComponent(NavigationComponent);
    fixture.detectChanges();
  });

  it('renders the four application menu entries in order', () => {
    const labels = Array.from(
      fixture.nativeElement.querySelectorAll('.nav-label') as NodeListOf<HTMLElement>,
      element => element.textContent?.trim()
    );

    expect(labels).toEqual(['Upload', 'Dashboard', 'Transactions', 'AI Insights']);
  });

  it('points each menu entry to its page route', () => {
    const links = Array.from(
      fixture.nativeElement.querySelectorAll('a.nav-item') as NodeListOf<HTMLAnchorElement>
    );

    expect(links.map(link => link.getAttribute('href'))).toEqual([
      '/upload',
      '/dashboard',
      '/transactions',
      '/ai-insights'
    ]);
  });

  it('navigates to AI Insights when its menu item is selected', async () => {
    const link = fixture.nativeElement.querySelector('a[href="/ai-insights"]') as HTMLAnchorElement;
    link.click();
    await fixture.whenStable();

    expect(router.url).toBe('/ai-insights');
  });

  it('marks the current menu entry as active', async () => {
    await router.navigateByUrl('/transactions');
    fixture.detectChanges();

    const activeLinks = Array.from(
      fixture.nativeElement.querySelectorAll('a.nav-item.active') as NodeListOf<HTMLAnchorElement>
    );
    expect(activeLinks.map(link => link.querySelector('.nav-label')?.textContent?.trim())).toEqual([
      'Transactions'
    ]);
  });
});
