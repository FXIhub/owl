uniform sampler2D cmap;
uniform sampler2D data;
uniform int norm;
uniform float vmin;
uniform float vmax;
uniform float gamma;
uniform int do_clamp;
uniform sampler2D mask;
uniform float maskedBits;
uniform float modelCenterX;
uniform float modelCenterY;
uniform float modelSize;
uniform float modelScale;
uniform int showModel;
uniform float imageShapeX;
uniform float imageShapeY;
uniform float modelVisibility;
void main()
{
  vec2 uv = gl_TexCoord[0].xy;
  vec4 color = texture2D(data, uv);
  vec4 mcolor = texture2D(mask, uv);
  float scale = (vmax-vmin);
  float offset = vmin;


  // Apply Model
  if((showModel == 1) && (uv[0] > modelVisibility)){
    //float s = modelSize*sqrt((uv[0]-modelCenterX)*(uv[0]-modelCenterX)+(uv[1]-modelCenterX)*(uv[1]-modelCenterX));
    float s = modelSize*sqrt((uv[0]-modelCenterX)*(uv[0]-modelCenterX)*(imageShapeX-1.)*(imageShapeX-1.)+(uv[1]-modelCenterY)*(uv[1]-modelCenterY)*(imageShapeY-1.)*(imageShapeY-1.));
    color.a = 3.0*(sin(s)-s*cos(s))/(s*s*s);
    color.a *= color.a * modelScale;

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
      gl_FragColor = texture2D(cmap, uv);
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
      gl_FragColor = texture2D(cmap, uv);
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
  color = texture2D(cmap, uv);
  gl_FragColor = color;
}
