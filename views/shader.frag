uniform sampler2D cmap;
uniform sampler2D data;
uniform int norm;
uniform float vmin;
uniform float vmax;
uniform float gamma;
uniform int do_clamp;
uniform int invert_colormap;
uniform sampler2D mask;
uniform float maskedBits;
uniform float modelCenterX;
uniform float modelCenterY;
uniform float modelSize;
uniform float modelScale;
uniform int showModel;
uniform int showModelPoisson;
uniform float imageShapeX;
uniform float imageShapeY;
uniform float modelVisibility;
uniform float modelMinimaAlpha;
uniform float fitMaskRadius;
uniform float detectorADUPhoton;
#define M_PI 3.1415926535897932384626433832795

vec4 colorLookup(in sampler2D colormap, in vec2 coord)
{
  if(invert_colormap != 0){
    coord[0] = 1.0-coord[0];
  }
  return texture2D(colormap, coord);
}

float rand(vec2 co){
    return fract(sin(dot(co.xy ,vec2(12.9898,78.233))) * 43758.5453);
}

float poisson(float x, vec2 co){
  co.x = floor(co.x * imageShapeX)/imageShapeX;
  co.y = floor(co.y * imageShapeY)/imageShapeY;
  x = x/detectorADUPhoton;
  float L = exp(-x);
  float k = 0.0;
  float p = 1.0;
  while(p > L){
    k = k + 1.0;
    co.x = rand(co);
    co.y = rand(co);
    p = p * co.x;
  }
  return (k-1.0)*detectorADUPhoton;
}

void main()
{
  vec2 uv = gl_TexCoord[0].xy;
  vec4 color = texture2D(data, uv);
  vec4 mcolor = texture2D(mask, uv);
  float scale = (vmax-vmin);
  float offset = vmin;
  
  float s;
  if(showModel == 1){
    // Paint Fit Mask Radius
    float r = sqrt((uv[0]-modelCenterX)*(uv[0]-modelCenterX)*(imageShapeX-1.)*(imageShapeX-1.)+(uv[1]-modelCenterY)*(uv[1]-modelCenterY)*(imageShapeY-1.)*(imageShapeY-1.));
    if(abs(r - fitMaskRadius) < 0.5){
      color.r = 1.0;
      color.g = 1.0;
      color.b = 1.0;
      color.a = 1.0;
      gl_FragColor = color;
      return;
    }

    // Paint Fit Model Minima
    s = 2.0*M_PI*modelSize*r;
    // We want to have a dashed line, with 40 dashes
    if(sin(atan(uv[1]-modelCenterY,uv[0]-modelCenterX) * 4.0*floor(0.5+r/16.0)) > 0.0){
      // d is the distance in pixel at which we want to test the function
      float d = 0.5;
      // Sphere diffraction has minimas at tan(s) == s
      float s_up = (r+d)*modelSize*2.0*M_PI;
      float err1 = abs(tan(s_up)-(s_up)) - abs(tan(s)-s);
      if(err1 > 0.0){
	float s_lo = (r-d)*modelSize*2.0*M_PI;;
	float err2 = abs(tan(s_lo)-(s_lo)) - abs(tan(s)-s);
	if(err2 > 0.0){
	  color.r = modelMinimaAlpha;
	  color.g = modelMinimaAlpha;
	  color.b = modelMinimaAlpha;
	  color.a = 1.0;
	  gl_FragColor = color;
	  return;
	}
      }
    }
  }
  
  // Apply Model
  if((showModel == 1) && (uv[0] > modelVisibility)){
    //float s = modelSize*sqrt((uv[0]-modelCenterX)*(uv[0]-modelCenterX)+(uv[1]-modelCenterX)*(uv[1]-modelCenterX));
    //    float s = modelSize*sqrt((uv[0]-modelCenterX)*(uv[0]-modelCenterX)*(imageShapeX-1.)*(imageShapeX-1.)+(uv[1]-modelCenterY)*(uv[1]-modelCenterY)*(imageShapeY-1.)*(imageShapeY-1.));
    color.a = 3.0*(sin(s)-s*cos(s))/(s*s*s);
    color.a *= color.a * modelScale;
    if (showModelPoisson == 1){
       color.a = poisson(color.a, uv);
    }

  }else{

    // Apply Mask

    // Using a float for the mask will only work up to about 24 bits
    float maskBits = mcolor.a;
    // loop through the first 16 bits
    float bit = 1.0;
    if(maskBits > 0.0){
      for(int i = 0;i<16;i++){
	if(floor(mod(maskBits/bit, 2.0)) == 1.0 && floor(mod(maskedBits/bit, 2.0)) == 1.0){
	  color.a = 0.0;
	  gl_FragColor = color;
	  return;
	}
	bit = bit*2.0;
      }
    }
  }


  uv[0] = (color.a-offset);

  // Check for clamping
  uv[1] = 0.0;
  if(uv[0] < 0.0){
    if(do_clamp == 1){
      uv[0] = 0.0;
      gl_FragColor = colorLookup(cmap, uv);
      return;
    }else{
      color.a = 0.0;
      gl_FragColor = color;
      return;
    }
  }
  if(uv[0] > scale){
    if(do_clamp == 1){
      uv[0] = 1.0;
      gl_FragColor = colorLookup(cmap, uv);
      return;
    }else{
      color.a = 0.0;
      gl_FragColor = color;
      return;
    }
  }
  // Apply Colormap
  if(norm == 0){
    // linear
    uv[0] /= scale;
  }else if(norm == 1){
    // log
    scale = log(scale+1.0);
    uv[0] = log(uv[0]+1.0)/scale;
  }else if(norm == 2){
    // power
    scale = pow(scale+1.0, gamma)-1.0;
    uv[0] = (pow(uv[0]+1.0, gamma)-1.0)/scale;
  }
  color = colorLookup(cmap, uv);
  gl_FragColor = color;
}
