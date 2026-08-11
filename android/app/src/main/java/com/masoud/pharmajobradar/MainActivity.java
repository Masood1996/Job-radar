package com.masoud.pharmajobradar;
import android.app.*;import android.os.*;import android.webkit.*;import android.view.*;
public class MainActivity extends Activity{
 WebView w;
 @Override public void onCreate(Bundle b){super.onCreate(b);w=new WebView(this);w.setWebViewClient(new WebViewClient());w.getSettings().setJavaScriptEnabled(true);w.getSettings().setDomStorageEnabled(true);w.loadUrl("https://YOUR-HOSTED-RADAR.example/");setContentView(w);}
 @Override public void onBackPressed(){if(w.canGoBack())w.goBack();else super.onBackPressed();}
}
