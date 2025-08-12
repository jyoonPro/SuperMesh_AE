/******************************************************************************
This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.
*******************************************************************************/

#pragma once

#include <tacos/topology/topology.h>

namespace tacos {

class FoldedTorus final : public Topology {
  public:
    FoldedTorus(int width, int height, Latency latency_high, Bandwidth bandwidth_high, Latency latency_low, Bandwidth bandwidth_low) noexcept;

  private:
    int width;
    int height;

};

}  // namespace tacos
